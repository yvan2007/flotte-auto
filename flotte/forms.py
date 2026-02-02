"""Formulaires FLOTTE — validation et champs pour véhicules, ventes, utilisateurs."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, Location, ImportDemarche, Depense, DocumentVehicule,
    Reparation, ProfilUtilisateur, Facture, Vente,
    RapportJournalier, Maintenance, ReleveCarburant, Conducteur,
)

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Formulaire de connexion (style FLOTTE)."""
    username = forms.CharField(
        label='Identifiant',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'ex. admin',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '•••',
            'autocomplete': 'current-password',
        })
    )


class UserCreateForm(UserCreationForm):
    """Création d'utilisateur (admin) avec rôle."""
    nom = forms.CharField(label='Nom affiché', max_length=120, required=False)
    role = forms.ChoiceField(
        label='Rôle',
        choices=ProfilUtilisateur.ROLE_CHOICES,
        initial='user'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Pour « Mot de passe oublié »'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'first_name') and self.cleaned_data.get('nom'):
                user.first_name = self.cleaned_data['nom']
                user.save(update_fields=['first_name'])
            ProfilUtilisateur.objects.get_or_create(
                user=user,
                defaults={'role': self.cleaned_data.get('role', 'user')}
            )
            # Mise à jour du rôle si le profil existait
            profil = user.profil_flotte
            profil.role = self.cleaned_data.get('role', 'user')
            profil.save()
        return user


class MarqueForm(forms.ModelForm):
    """Une même marque ne peut pas exister deux fois."""
    class Meta:
        model = Marque
        fields = ('nom', 'archive')
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex. Toyota'}),
            'archive': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        help_texts = {'nom': "Une même marque ne peut pas exister deux fois dans la base."}

    def clean_nom(self):
        nom = (self.cleaned_data.get('nom') or '').strip()
        if not nom:
            raise forms.ValidationError('Le nom est obligatoire.')
        qs = Marque.objects.filter(nom__iexact=nom)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Une marque avec ce nom existe déjà.')
        return nom


class ModeleForm(forms.ModelForm):
    """Version et année obligatoires ; un même modèle ne peut exister qu'une fois par marque."""
    class Meta:
        model = Modele
        fields = ('marque', 'nom', 'version', 'annee_min', 'annee_max', 'archive')
        widgets = {
            'marque': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-input'}),
            'version': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex. Berline'}),
            'annee_min': forms.NumberInput(attrs={'class': 'form-input', 'min': 1900, 'max': 2030}),
            'annee_max': forms.NumberInput(attrs={'class': 'form-input', 'min': 1900, 'max': 2030}),
            'archive': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        help_texts = {
            'version': 'Champ obligatoire.',
            'annee_min': 'Champ obligatoire. Un même modèle ne peut exister qu\'une fois par marque.',
        }

    def clean_version(self):
        version = (self.cleaned_data.get('version') or '').strip()
        if not version:
            raise forms.ValidationError('La version est obligatoire.')
        return version


class TypeCarburantForm(forms.ModelForm):
    class Meta:
        model = TypeCarburant
        fields = ('libelle',)
        widgets = {'libelle': forms.TextInput(attrs={'class': 'form-input'})}


class TypeTransmissionForm(forms.ModelForm):
    class Meta:
        model = TypeTransmission
        fields = ('libelle',)
        widgets = {'libelle': forms.TextInput(attrs={'class': 'form-input'})}


class TypeVehiculeForm(forms.ModelForm):
    class Meta:
        model = TypeVehicule
        fields = ('libelle',)
        widgets = {'libelle': forms.TextInput(attrs={'class': 'form-input'})}


class VehiculeForm(forms.ModelForm):
    """Formulaire véhicule — châssis = identifiant principal (surtout en import sans immat.)."""
    class Meta:
        model = Vehicule
        fields = (
            'numero_chassis', 'marque', 'modele', 'annee', 'statut',
            'type_vehicule', 'type_carburant', 'type_transmission',
            'couleur_exterieure', 'couleur_interieure',
            'date_entree_parc', 'km_entree', 'kilometrage_actuel',
            'prix_achat', 'origine_pays', 'etat_entree',
            'numero_immatriculation', 'date_premiere_immat',
            'consommation_moyenne', 'rejet_co2', 'puissance_fiscale',
            'km_prochaine_vidange',
        )
        labels = {'origine_pays': "Pays d'origine ou d'achat", 'statut': 'Statut (ex. en cours d\'importation)'}
        widgets = {
            'numero_chassis': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex. WDD2050461A123456'}),
            'marque': forms.Select(attrs={'class': 'form-select'}),
            'modele': forms.Select(attrs={'class': 'form-select'}),
            'annee': forms.NumberInput(attrs={'class': 'form-input', 'min': 1990, 'max': 2030}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'type_vehicule': forms.Select(attrs={'class': 'form-select'}),
            'type_carburant': forms.Select(attrs={'class': 'form-select'}),
            'type_transmission': forms.Select(attrs={'class': 'form-select'}),
            'couleur_exterieure': forms.TextInput(attrs={'class': 'form-input'}),
            'couleur_interieure': forms.TextInput(attrs={'class': 'form-input'}),
            'date_entree_parc': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'km_entree': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'kilometrage_actuel': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1000}),
            'origine_pays': forms.TextInput(attrs={'class': 'form-input'}),
            'etat_entree': forms.Select(attrs={'class': 'form-select'}),
            'numero_immatriculation': forms.TextInput(attrs={'class': 'form-input'}),
            'date_premiere_immat': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'consommation_moyenne': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 0.1}),
            'rejet_co2': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'puissance_fiscale': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'km_prochaine_vidange': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['marque'].queryset = Marque.objects.filter(archive=False).order_by('nom')
        # Modèles : filtrés par marque sélectionnée (logique métier marque → modèles)
        marque_id = None
        if self.instance and self.instance.pk and self.instance.marque_id:
            marque_id = self.instance.marque_id
        elif self.data.get('marque'):
            try:
                marque_id = int(self.data['marque'])
            except (ValueError, TypeError):
                pass
        if marque_id is not None:
            self.fields['modele'].queryset = Modele.objects.filter(marque_id=marque_id, archive=False).order_by('nom')
        else:
            self.fields['modele'].queryset = Modele.objects.filter(marque__archive=False, archive=False).order_by('marque__nom', 'nom')
        self.fields['etat_entree'].widget = forms.Select(
            choices=[
                ('', '—'),
                ('Très bon', 'Très bon'),
                ('Bon', 'Bon'),
                ('Correct', 'Correct'),
                ('À réparer', 'À réparer'),
            ],
            attrs={'class': 'form-select'}
        )


class LocationForm(forms.ModelForm):
    """Formulaire location avec CT, assurance, km vidange."""
    class Meta:
        model = Location
        fields = (
            'vehicule', 'locataire', 'type_location', 'date_debut', 'date_fin',
            'loyer_mensuel', 'km_inclus_mois', 'prix_km_supplementaire',
            'date_expiration_ct', 'date_expiration_assurance', 'km_prochaine_vidange',
            'remarques', 'statut',
        )
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'locataire': forms.TextInput(attrs={'class': 'form-input'}),
            'type_location': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'km_inclus_mois': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prix_km_supplementaire': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'date_expiration_ct': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_expiration_assurance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'km_prochaine_vidange': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'remarques': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Véhicules éligibles : au parc (nouvelle location) ou véhicule courant (modification)
        from django.db.models import Q
        qs = Vehicule.objects.filter(statut='parc').order_by('marque__nom', 'modele__nom')
        if self.instance and self.instance.pk and self.instance.vehicule_id:
            qs = Vehicule.objects.filter(Q(statut='parc') | Q(pk=self.instance.vehicule_id)).distinct().order_by('marque__nom', 'modele__nom')
        self.fields['vehicule'].queryset = qs
        self.fields['type_location'].widget = forms.Select(
            choices=[
                ('LLD', 'LLD (Location Longue Durée)'),
                ('LOA', 'LOA (Location avec Option d\'Achat)'),
                ('Location courte', 'Location courte'),
            ],
            attrs={'class': 'form-select'}
        )


class ImportDemarcheForm(forms.ModelForm):
    class Meta:
        model = ImportDemarche
        fields = ('etape', 'date_etape', 'statut_etape', 'remarque')
        widgets = {
            'etape': forms.TextInput(attrs={'class': 'form-input'}),
            'date_etape': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'statut_etape': forms.TextInput(attrs={'class': 'form-input'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ('date_vente', 'acquereur', 'prix_vente', 'km_vente', 'garantie_duree', 'etat_livraison')
        widgets = {
            'date_vente': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'acquereur': forms.TextInput(attrs={'class': 'form-input'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'km_vente': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'garantie_duree': forms.TextInput(attrs={'class': 'form-input'}),
            'etat_livraison': forms.TextInput(attrs={'class': 'form-input'}),
        }


class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ('type_depense', 'libelle', 'phase', 'montant', 'date_depense', 'remarque')
        widgets = {
            'type_depense': forms.Select(attrs={'class': 'form-select'}),
            'libelle': forms.TextInput(attrs={'class': 'form-input'}),
            'phase': forms.TextInput(attrs={'class': 'form-input'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'date_depense': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class DocumentVehiculeForm(forms.ModelForm):
    """Document disponible ou à faire (assurance, carte grise, CT…)."""
    class Meta:
        model = DocumentVehicule
        fields = ('type_document', 'numero', 'date_emission', 'date_echeance', 'disponible', 'remarque')
        widgets = {
            'type_document': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex. Carte grise, Assurance, CT'}),
            'numero': forms.TextInput(attrs={'class': 'form-input'}),
            'date_emission': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }
        labels = {'disponible': 'Disponible (décoché = document à faire)'}


class ReparationForm(forms.ModelForm):
    class Meta:
        model = Reparation
        fields = (
            'date_reparation', 'kilometrage', 'type_rep', 'description',
            'cout', 'prestataire', 'a_faire',
        )
        widgets = {
            'date_reparation': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'kilometrage': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'type_rep': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'cout': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prestataire': forms.TextInput(attrs={'class': 'form-input'}),
            'a_faire': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class UserUpdateForm(forms.ModelForm):
    """Modification d'un utilisateur (nom, rôle, actif). Archiver = décocher Compte actif."""
    role = forms.ChoiceField(
        label='Rôle',
        choices=ProfilUtilisateur.ROLE_CHOICES,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'is_active', 'role')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Requis pour « Mot de passe oublié »'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'is_active': 'Compte actif (décocher pour archiver l\'utilisateur)', 'email': 'Email (pour réinitialisation mot de passe)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.initial['role'] = self.instance.profil_flotte.role
            except ProfilUtilisateur.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'profil_flotte'):
            user.profil_flotte.role = self.cleaned_data.get('role', 'user')
            user.profil_flotte.save()
        return user


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ('numero', 'fournisseur', 'date_facture', 'montant', 'type_facture', 'remarque')
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-input'}),
            'fournisseur': forms.TextInput(attrs={'class': 'form-input'}),
            'date_facture': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'type_facture': forms.TextInput(attrs={'class': 'form-input'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class RapportJournalierForm(forms.ModelForm):
    """Upload rapport journalier ou document CA (PDF)."""
    class Meta:
        model = RapportJournalier
        fields = ('date_rapport', 'titre', 'type_rapport', 'fichier', 'remarque')
        widgets = {
            'date_rapport': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'titre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex. Rapport journalier 01/02/2026'}),
            'type_rapport': forms.Select(attrs={'class': 'form-select'}),
            'fichier': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class MaintenanceForm(forms.ModelForm):
    """Maintenance préventive par véhicule."""
    class Meta:
        model = Maintenance
        fields = (
            'vehicule', 'type_maintenance', 'date_prevue', 'kilometrage_prevu',
            'date_effectuee', 'kilometrage_effectue', 'cout', 'prestataire',
            'statut', 'remarque',
        )
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'type_maintenance': forms.Select(attrs={'class': 'form-select'}),
            'date_prevue': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'kilometrage_prevu': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'date_effectuee': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'kilometrage_effectue': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'cout': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prestataire': forms.TextInput(attrs={'class': 'form-input'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicule'].queryset = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')


class ReleveCarburantForm(forms.ModelForm):
    """Relevé carburant par véhicule."""
    class Meta:
        model = ReleveCarburant
        fields = (
            'vehicule', 'date_releve', 'kilometrage', 'litres', 'montant_fcfa',
            'prix_litre', 'lieu', 'remarque',
        )
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'date_releve': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'kilometrage': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'litres': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 0.01}),
            'montant_fcfa': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prix_litre': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'lieu': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Station'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicule'].queryset = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')


class ConducteurForm(forms.ModelForm):
    """Conducteur (chauffeur)."""
    class Meta:
        model = Conducteur
        fields = (
            'nom', 'prenom', 'email', 'telephone',
            'permis_numero', 'permis_date_expiration', 'actif', 'remarque',
        )
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input'}),
            'prenom': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'telephone': forms.TextInput(attrs={'class': 'form-input'}),
            'permis_numero': forms.TextInput(attrs={'class': 'form-input'}),
            'permis_date_expiration': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }
