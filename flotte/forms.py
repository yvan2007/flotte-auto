"""Formulaires FLOTTE — validation et champs pour véhicules, ventes, utilisateurs."""
import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import DatabaseError
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django_countries import countries
from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, Location, ImportDemarche, Depense, DocumentVehicule,
    Reparation, ProfilUtilisateur, Facture, Vente,
    RapportJournalier, Maintenance, ReleveCarburant, Conducteur,
    ChargeImport, PartieImportee, Contravention, TypeDocument,
    PhotoVehicule, PenaliteFacture,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# Liste des couleurs pour le select véhicule (extérieure / intérieure)
COULEURS_VEHICULE = [
    '', 'Blanc', 'Noir', 'Gris', 'Bleu', 'Rouge', 'Argent', 'Vert', 'Beige',
    'Jaune', 'Orange', 'Marron', 'Bordeaux', 'Or', 'Ivoire', 'Autre',
]

# Liste de tous les pays (noms triés) pour datalist pays d'origine
_LISTE_PAYS = None

# ——— Listes de suggestions pour champs avec datalist (menu déroulant + saisie libre) ———
ETAPES_IMPORT = [
    'Dédouanement', 'Transport international', 'Contrôle technique', 'Immatriculation',
    'Réception véhicule', 'Vérification douane', 'Paiement taxes', 'Autre',
]
STATUTS_ETAPE_IMPORT = ['En attente', 'En cours', 'Terminé', 'Refusé', 'Reporté']
GARANTIES_VENTE = ['Aucune', '3 mois', '6 mois', '1 an', '2 ans', 'Constructeur']
ETATS_LIVRAISON = ['Bon état', 'Très bon état', 'Parfait', 'Rayures', 'Choc réparé', 'Comme neuf']
PHASES_DEPENSE = ['Import', 'Réparation', 'Préparation', 'Contrôle', 'Livraison', 'Stock', 'Autre']
TYPES_REPARATION = [
    'Carrosserie', 'Mécanique', 'Freinage', 'Distribution', 'Climatisation',
    'Électricité', 'Pneumatiques', 'Vidange', 'Amortisseurs', 'Autre',
]
TYPES_FACTURE = ['Achat', 'Réparation', 'Assurance', 'Entretien', 'Pièces', 'Carburant', 'Autre']


def get_liste_pays():
    """Retourne la liste triée des noms de pays (ISO 3166-1)."""
    global _LISTE_PAYS
    if _LISTE_PAYS is None:
        _LISTE_PAYS = sorted([name for _code, name in countries])
    return _LISTE_PAYS


class PaysOrigineDatalistWidget(forms.TextInput):
    """
    Champ texte avec datalist HTML5 : en tapant, le navigateur propose
    les pays de la liste (tous les pays du monde).
    """
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        field_id = attrs.get('id', 'id_origine_pays')
        datalist_id = f'{field_id}_datalist'
        attrs.setdefault('list', datalist_id)
        attrs.setdefault('class', 'form-input')
        attrs.setdefault('placeholder', "Tapez pour afficher les pays…")
        attrs.setdefault('autocomplete', 'off')  # évite conflit avec l'autocomplete navigateur
        input_html = super().render(name, value, attrs, renderer)
        options = ''.join(
            format_html('<option value="{}">', escape(pays))
            for pays in get_liste_pays()
        )
        datalist_html = format_html(
            '<datalist id="{}">{}</datalist>',
            datalist_id,
            mark_safe(options),
        )
        return mark_safe(input_html + datalist_html)


class DatalistWidget(forms.TextInput):
    """
    Champ texte avec datalist HTML5 : suggestions au fur et à mesure de la frappe,
    avec possibilité de saisir une valeur libre. choices = liste de chaînes.
    """
    def __init__(self, choices=None, attrs=None, **kwargs):
        super().__init__(attrs=attrs, **kwargs)
        self.choices = list(choices) if choices else []

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        field_id = attrs.get('id', f'id_{name}')
        datalist_id = f'{field_id}_datalist'
        attrs = {**attrs, 'list': datalist_id, 'autocomplete': 'off'}
        attrs.setdefault('class', 'form-input')
        input_html = super().render(name, value, attrs, renderer)
        # Valeurs uniques non vides, triées
        options = sorted({str(c).strip() for c in self.choices if c and str(c).strip()})
        options_html = ''.join(
            format_html('<option value="{}">', escape(o))
            for o in options
        )
        datalist_html = format_html(
            '<datalist id="{}">{}</datalist>',
            datalist_id,
            mark_safe(options_html),
        )
        return mark_safe(input_html + datalist_html)


class LoginForm(AuthenticationForm):
    """Formulaire de connexion (style FLOTTE). Accepte identifiant OU email."""
    username = forms.CharField(
        label='Identifiant ou email',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Identifiant ou adresse email',
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

    def clean_username(self):
        """Si la valeur ressemble à un email, résoudre vers le username du compte."""
        value = self.cleaned_data.get('username')
        if not value:
            return value
        value = value.strip()
        if '@' in value:
            user = User.objects.filter(email__iexact=value).first()
            if user:
                return user.username
        return value


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


class TypeDocumentForm(forms.ModelForm):
    class Meta:
        model = TypeDocument
        fields = ('libelle', 'ordre')
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-input'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


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
            'km_prochaine_vidange', 'date_expiration_ct', 'date_expiration_assurance',
        )
        labels = {
            'origine_pays': "Pays d'origine ou d'achat",
            'statut': 'Statut (ex. en cours d\'importation)',
            'date_expiration_ct': 'Date expiration CT (véhicule au parc)',
            'date_expiration_assurance': 'Date expiration assurance (véhicule au parc)',
        }
        help_texts = {
            'origine_pays': "Tapez pour afficher la liste, puis sélectionnez un pays.",
        }
        widgets = {
            'numero_chassis': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex. WDD2050461A123456'}),
            'marque': forms.Select(attrs={'class': 'form-select'}),
            'modele': forms.Select(attrs={'class': 'form-select'}),
            'annee': forms.NumberInput(attrs={'class': 'form-input', 'min': 1990, 'max': 2030}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'type_vehicule': forms.Select(attrs={'class': 'form-select'}),
            'type_carburant': forms.Select(attrs={'class': 'form-select'}),
            'type_transmission': forms.Select(attrs={'class': 'form-select'}),
            'couleur_exterieure': forms.Select(attrs={'class': 'form-select'}),
            'couleur_interieure': forms.Select(attrs={'class': 'form-select'}),
            'date_entree_parc': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'km_entree': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'kilometrage_actuel': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1000}),
            'origine_pays': PaysOrigineDatalistWidget(),
            'etat_entree': forms.Select(attrs={'class': 'form-select'}),
            'numero_immatriculation': forms.TextInput(attrs={'class': 'form-input'}),
            'date_premiere_immat': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'consommation_moyenne': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 0.1}),
            'rejet_co2': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'puissance_fiscale': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'km_prochaine_vidange': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'date_expiration_ct': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_expiration_assurance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
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
        # Couleurs en select (liste déroulante) — inclure valeur existante si hors liste
        base_choix = [('', '—')] + [(c, c) for c in COULEURS_VEHICULE if c]
        for fname in ('couleur_exterieure', 'couleur_interieure'):
            val = (self.instance.pk and getattr(self.instance, fname, None)) or (self.data.get(fname) if self.data else None)
            if val and val.strip() and not any(c[0] == val for c in base_choix):
                choix = [('', '—'), (val, val)] + [(c, c) for c in COULEURS_VEHICULE if c]
            else:
                choix = base_choix
            self.fields[fname].widget = forms.Select(choices=choix, attrs={'class': 'form-select'})

    def clean_origine_pays(self):
        """Éviter qu'un montant (nombre) soit saisi par erreur dans le pays d'origine."""
        value = (self.cleaned_data.get('origine_pays') or '').strip()
        if not value:
            return value
        if value.isdigit():
            raise forms.ValidationError(
                'Saisir un nom de pays (ex. Allemagne, Japon), pas un nombre. '
                'Le prix d\'achat se renseigne dans le champ « Prix d\'achat ».'
            )
        return value


class LocationForm(forms.ModelForm):
    """Formulaire location avec CT, assurance, km vidange, conducteur assigné."""
    class Meta:
        model = Location
        fields = (
            'vehicule', 'conducteur', 'locataire', 'type_location', 'date_debut', 'date_fin',
            'loyer_mensuel', 'cout_location', 'frais_annexes',
            'km_inclus_mois', 'prix_km_supplementaire',
            'date_expiration_ct', 'date_expiration_assurance', 'km_prochaine_vidange',
            'remarques', 'statut',
        )
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'conducteur': forms.Select(attrs={'class': 'form-select'}),
            'locataire': forms.TextInput(attrs={'class': 'form-input'}),
            'type_location': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'cout_location': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'frais_annexes': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
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
        self.fields['conducteur'].queryset = Conducteur.objects.filter(actif=True).order_by('nom', 'prenom')
        self.fields['conducteur'].required = False
        self.fields['type_location'].widget = forms.Select(
            choices=[
                ('LLD', 'LLD (Location Longue Durée)'),
                ('LOA', 'LOA (Location avec Option d\'Achat)'),
                ('Location courte', 'Location courte'),
            ],
            attrs={'class': 'form-select'}
        )
        # Locataire : suggestions des noms déjà saisis + saisie libre
        try:
            locataires = sorted(
                Location.objects.exclude(locataire='')
                .values_list('locataire', flat=True)
                .distinct()
            )
            self.fields['locataire'].widget = DatalistWidget(choices=locataires, attrs={'class': 'form-input', 'placeholder': 'Nom du locataire'})
        except (DatabaseError, Exception):
            self.fields['locataire'].widget = DatalistWidget(choices=[], attrs={'class': 'form-input'})


class ImportDemarcheForm(forms.ModelForm):
    class Meta:
        model = ImportDemarche
        fields = ('etape', 'date_etape', 'statut_etape', 'fichier', 'remarque')
        widgets = {
            'etape': DatalistWidget(choices=ETAPES_IMPORT, attrs={'class': 'form-input', 'placeholder': 'Ex. Dédouanement, Immatriculation'}),
            'date_etape': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'statut_etape': DatalistWidget(choices=STATUTS_ETAPE_IMPORT, attrs={'class': 'form-input', 'placeholder': 'Ex. En cours, Terminé'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'application/pdf,image/*'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class VenteForm(forms.ModelForm):
    """Formulaire vente : optionnellement lier à un compte client (acquéreur)."""
    class Meta:
        model = Vente
        fields = ('date_vente', 'acquereur', 'acquereur_compte', 'prix_vente', 'km_vente', 'garantie_duree', 'etat_livraison')
        widgets = {
            'date_vente': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'acquereur': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom de l\'acquéreur'}),
            'acquereur_compte': forms.Select(attrs={'class': 'form-select'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'km_vente': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'garantie_duree': DatalistWidget(choices=GARANTIES_VENTE, attrs={'class': 'form-input', 'placeholder': 'Ex. 6 mois, 1 an'}),
            'etat_livraison': DatalistWidget(choices=ETATS_LIVRAISON, attrs={'class': 'form-input', 'placeholder': 'Ex. Très bon état'}),
        }
        labels = {
            'acquereur_compte': 'Compte client (acquéreur)',
        }
        help_texts = {
            'acquereur_compte': 'Optionnel. Si l\'acquéreur a un compte Utilisateur, associez-le pour qu\'il voie cette vente.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['acquereur_compte'].required = False
        self.fields['acquereur_compte'].empty_label = '— Aucun compte client —'
        # Queryset : seuls les comptes avec rôle Utilisateur (client), avec gestion d'exceptions
        try:
            self.fields['acquereur_compte'].queryset = User.objects.filter(
                profil_flotte__role='user',
                is_active=True,
            ).select_related('profil_flotte').order_by('username')
        except (DatabaseError, Exception) as e:
            logger.warning('VenteForm: impossible de charger la liste des comptes clients: %s', e)
            self.fields['acquereur_compte'].queryset = User.objects.none()

    def clean_acquereur_compte(self):
        """Vérifie que le compte sélectionné a bien le rôle Utilisateur (sécurité si formulaire modifié)."""
        value = self.cleaned_data.get('acquereur_compte')
        if not value:
            return value
        try:
            if hasattr(value, 'profil_flotte') and value.profil_flotte.role != 'user':
                raise forms.ValidationError('Seul un compte client (rôle Utilisateur) peut être associé.')
        except (ProfilUtilisateur.DoesNotExist, AttributeError):
            raise forms.ValidationError('Compte invalide pour une association acquéreur.')
        return value


class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ('type_depense', 'libelle', 'phase', 'montant', 'date_depense', 'remarque')
        widgets = {
            'type_depense': forms.Select(attrs={'class': 'form-select'}),
            'libelle': forms.TextInput(attrs={'class': 'form-input'}),
            'phase': DatalistWidget(choices=PHASES_DEPENSE, attrs={'class': 'form-input', 'placeholder': 'Ex. Import, Réparation'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'date_depense': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class DocumentVehiculeForm(forms.ModelForm):
    """Document disponible ou à faire — type depuis liste ou libre (autre), avec fichier optionnel."""
    class Meta:
        model = DocumentVehicule
        fields = ('type_document_fk', 'type_document', 'numero', 'date_emission', 'date_echeance', 'disponible', 'fichier', 'remarque')
        widgets = {
            'type_document_fk': forms.Select(attrs={'class': 'form-select'}),
            'type_document': DatalistWidget(choices=[], attrs={'class': 'form-input', 'placeholder': 'Si "Autre", choisir ou saisir le type'}),
            'numero': forms.TextInput(attrs={'class': 'form-input'}),
            'date_emission': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'application/pdf,image/*'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }
        labels = {
            'disponible': 'Disponible (décoché = document à faire)',
            'type_document_fk': 'Type de document',
            'type_document': 'Type (si Autre)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_document_fk'].queryset = TypeDocument.objects.all()
        self.fields['type_document_fk'].empty_label = '— Autre (saisir ci-dessous)'
        self.fields['type_document_fk'].required = False
        self.fields['type_document'].required = False
        # Suggestions type document = libellés des types existants (pour saisie "Autre")
        try:
            types_doc = list(TypeDocument.objects.values_list('libelle', flat=True).order_by('libelle'))
            self.fields['type_document'].widget = DatalistWidget(choices=types_doc, attrs={'class': 'form-input', 'placeholder': 'Si "Autre", choisir ou saisir le type'})
        except (DatabaseError, Exception):
            pass

    def clean(self):
        data = super().clean()
        type_libre = (data.get('type_document') or '').strip()
        if not data.get('type_document_fk') and not type_libre:
            self.add_error('type_document_fk', 'Choisir un type dans la liste ou saisir un type dans "Type (si Autre)".')
        return data


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
            'type_rep': DatalistWidget(choices=TYPES_REPARATION, attrs={'class': 'form-input', 'placeholder': 'Ex. Carrosserie, Mécanique'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'cout': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'prestataire': DatalistWidget(choices=[], attrs={'class': 'form-input', 'placeholder': 'Nom du prestataire'}),
            'a_faire': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            prestataires = sorted(
                Reparation.objects.exclude(prestataire='')
                .values_list('prestataire', flat=True)
                .distinct()
            )
            self.fields['prestataire'].widget = DatalistWidget(choices=prestataires, attrs={'class': 'form-input', 'placeholder': 'Nom du prestataire'})
        except (DatabaseError, Exception):
            pass


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
        fields = ('numero', 'fournisseur', 'date_facture', 'montant', 'type_facture', 'fichier', 'remarque')
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-input'}),
            'fournisseur': DatalistWidget(choices=[], attrs={'class': 'form-input', 'placeholder': 'Nom du fournisseur'}),
            'date_facture': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'type_facture': DatalistWidget(choices=TYPES_FACTURE, attrs={'class': 'form-input', 'placeholder': 'Ex. Achat, Réparation'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'application/pdf,image/*'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            fournisseurs = sorted(
                Facture.objects.exclude(fournisseur='')
                .values_list('fournisseur', flat=True)
                .distinct()
            )
            self.fields['fournisseur'].widget = DatalistWidget(choices=fournisseurs, attrs={'class': 'form-input', 'placeholder': 'Nom du fournisseur'})
        except (DatabaseError, Exception):
            pass


class PenaliteFactureForm(forms.ModelForm):
    """Pénalité liée à une facture (retard, amende, etc.)."""
    class Meta:
        model = PenaliteFacture
        fields = ('date_penalite', 'libelle', 'montant', 'remarque')
        widgets = {
            'date_penalite': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'libelle': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Retard de paiement, Amende'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
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
            'prestataire': DatalistWidget(choices=[], attrs={'class': 'form-input', 'placeholder': 'Nom du prestataire'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicule'].queryset = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')
        try:
            m = list(Maintenance.objects.exclude(prestataire='').values_list('prestataire', flat=True))
            r = list(Reparation.objects.exclude(prestataire='').values_list('prestataire', flat=True))
            prestataires = sorted(set(m + r))
            self.fields['prestataire'].widget = DatalistWidget(choices=prestataires, attrs={'class': 'form-input', 'placeholder': 'Nom du prestataire'})
        except (DatabaseError, Exception):
            pass


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
            'lieu': DatalistWidget(choices=[], attrs={'class': 'form-input', 'placeholder': 'Station ou lieu'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicule'].queryset = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')
        try:
            lieux = sorted(
                ReleveCarburant.objects.exclude(lieu='')
                .values_list('lieu', flat=True)
                .distinct()
            )
            self.fields['lieu'].widget = DatalistWidget(choices=lieux, attrs={'class': 'form-input', 'placeholder': 'Station ou lieu'})
        except (DatabaseError, Exception):
            pass


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


class ChargeImportForm(forms.ModelForm):
    """Charges d'importation : fret, dédouanement, transitaire, coût total."""
    class Meta:
        model = ChargeImport
        fields = ('fret', 'frais_dedouanement', 'frais_transitaire', 'cout_total', 'remarque')
        widgets = {
            'fret': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'frais_dedouanement': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'frais_transitaire': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'cout_total': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class PartieImporteeForm(forms.ModelForm):
    """Pièce ou partie de véhicule importée."""
    class Meta:
        model = PartieImportee
        fields = ('vehicule', 'designation', 'quantite', 'cout_unitaire', 'remarque')
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-input'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'cout_unitaire': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.vehicule_filtre = kwargs.pop('vehicule_filtre', None)
        super().__init__(*args, **kwargs)
        qs = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')
        if self.vehicule_filtre:
            self.fields['vehicule'].initial = self.vehicule_filtre
        self.fields['vehicule'].queryset = qs


class ContraventionForm(forms.ModelForm):
    """Contravention / amende liée à une location."""
    class Meta:
        model = Contravention
        fields = ('date_contravention', 'reference', 'montant', 'lieu', 'remarque')
        widgets = {
            'date_contravention': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'N° PV'}),
            'montant': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'lieu': forms.TextInput(attrs={'class': 'form-input'}),
            'remarque': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class PhotoVehiculeForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier une photo de véhicule."""
    class Meta:
        model = PhotoVehicule
        fields = ('photo', 'angle', 'description', 'est_principale', 'ordre')
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
            'angle': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Description optionnelle (ex: "Vue avant avec phares allumés")'
            }),
            'est_principale': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'placeholder': '0'
            }),
        }
