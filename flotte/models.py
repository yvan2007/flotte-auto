"""
Modèles FLOTTE — Marques, modèles, types, véhicules (châssis = identifiant),
locations (CT, assurance, km vidange), import, dépenses, documents, réparations.
"""
from django.db import models
from django.conf import settings


class Marque(models.Model):
    """Marque automobile (archivable)."""
    nom = models.CharField('Nom', max_length=120, unique=True)
    archive = models.BooleanField('Archivée', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Marque'
        verbose_name_plural = 'Marques'

    def __str__(self):
        return self.nom


class Modele(models.Model):
    """Modèle lié à une marque (unicité marque + nom). Version et année obligatoires."""
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE, related_name='modeles')
    nom = models.CharField('Nom', max_length=120)
    version = models.CharField('Version', max_length=80)
    annee_min = models.PositiveIntegerField('Année min', default=2000)
    annee_max = models.PositiveIntegerField('Année max', null=True, blank=True)
    archive = models.BooleanField('Archivé', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['marque__nom', 'nom']
        unique_together = [['marque', 'nom']]
        verbose_name = 'Modèle'
        verbose_name_plural = 'Modèles'

    def __str__(self):
        return f'{self.marque.nom} {self.nom}'


class TypeCarburant(models.Model):
    """Type de carburant / énergie (essence, diesel, électrique, etc.)."""
    libelle = models.CharField('Libellé', max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = 'Type de carburant'
        verbose_name_plural = 'Types de carburant'

    def __str__(self):
        return self.libelle


class TypeTransmission(models.Model):
    """Type de transmission (manuelle, automatique, etc.)."""
    libelle = models.CharField('Libellé', max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = 'Type de transmission'
        verbose_name_plural = 'Types de transmission'

    def __str__(self):
        return self.libelle


class TypeVehicule(models.Model):
    """Type de véhicule (voiture, SUV, utilitaire, etc.)."""
    libelle = models.CharField('Libellé', max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = 'Type de véhicule'
        verbose_name_plural = 'Types de véhicule'

    def __str__(self):
        return self.libelle


class Vehicule(models.Model):
    """Véhicule — numéro de châssis = identifiant principal."""
    STATUT_CHOICES = [
        ('parc', 'Au parc'),
        ('import', 'En cours d\'importation'),
        ('vendu', 'Vendu'),
    ]
    numero_chassis = models.CharField(
        'Numéro de châssis',
        max_length=80,
        unique=True,
        help_text='Identifiant principal du véhicule (surtout en import sans immat.)'
    )
    marque = models.ForeignKey(
        Marque, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicules'
    )
    modele = models.ForeignKey(
        Modele, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicules'
    )
    annee = models.PositiveIntegerField('Année', null=True, blank=True)
    type_vehicule = models.ForeignKey(
        TypeVehicule, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicules'
    )
    type_carburant = models.ForeignKey(
        TypeCarburant, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicules'
    )
    type_transmission = models.ForeignKey(
        TypeTransmission, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicules'
    )
    couleur_exterieure = models.CharField('Couleur extérieure', max_length=60, blank=True)
    couleur_interieure = models.CharField('Couleur intérieure', max_length=60, blank=True)
    date_entree_parc = models.DateField('Date entrée parc', null=True, blank=True)
    km_entree = models.PositiveIntegerField('Km à l\'entrée', default=0)
    kilometrage_actuel = models.PositiveIntegerField('Kilométrage actuel', default=0)
    prix_achat = models.DecimalField(
        'Prix d\'achat (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    origine_pays = models.CharField('Pays d\'origine', max_length=80, blank=True)
    etat_entree = models.CharField('État à l\'entrée', max_length=40, blank=True)
    statut = models.CharField(
        'Statut', max_length=20, choices=STATUT_CHOICES, default='parc'
    )
    numero_immatriculation = models.CharField(
        'N° immatriculation', max_length=20, blank=True
    )
    date_premiere_immat = models.DateField(
        'Date première immatriculation', null=True, blank=True
    )
    consommation_moyenne = models.DecimalField(
        'Consommation (L/100km)', max_digits=5, decimal_places=2, null=True, blank=True
    )
    rejet_co2 = models.PositiveIntegerField('Rejet CO2 (g/km)', null=True, blank=True)
    puissance_fiscale = models.PositiveIntegerField('Puissance fiscale (CV)', null=True, blank=True)
    km_prochaine_vidange = models.PositiveIntegerField(
        'Kilométrage prochaine vidange', null=True, blank=True,
        help_text='Km auquel effectuer la prochaine vidange (si hors location)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_entree_parc', '-id']
        verbose_name = 'Véhicule'
        verbose_name_plural = 'Véhicules'

    def __str__(self):
        parts = []
        if self.marque:
            parts.append(self.marque.nom)
        if self.modele:
            parts.append(self.modele.nom)
        if parts:
            return f'{" ".join(parts)} — {self.numero_chassis}'
        return self.numero_chassis

    @property
    def libelle_court(self):
        """Marque + Modèle pour affichage."""
        if self.marque and self.modele:
            return f'{self.marque.nom} {self.modele.nom}'
        if self.marque:
            return self.marque.nom
        return self.numero_chassis


class ImportDemarche(models.Model):
    """Étape d'import / démarche par véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='import_demarches'
    )
    etape = models.CharField('Étape', max_length=80)
    date_etape = models.DateField('Date', null=True, blank=True)
    statut_etape = models.CharField('Statut étape', max_length=40, blank=True)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicule', 'id']
        verbose_name = 'Démarche import'
        verbose_name_plural = 'Démarches import'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.etape}'


class Depense(models.Model):
    """Dépense liée à un véhicule (entretien, réparation, carburant, assurance, etc.)."""
    TYPE_DEPENSE_CHOICES = [
        ('entretien', 'Entretien'),
        ('reparation', 'Réparation'),
        ('carburant', 'Carburant'),
        ('assurance', 'Assurance'),
        ('autre', 'Autre'),
    ]
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='depenses'
    )
    type_depense = models.CharField(
        'Type', max_length=20, choices=TYPE_DEPENSE_CHOICES, default='autre'
    )
    libelle = models.CharField('Libellé', max_length=200)
    phase = models.CharField('Phase', max_length=80, blank=True)
    montant = models.DecimalField('Montant (FCFA)', max_digits=14, decimal_places=0)
    date_depense = models.DateField('Date', null=True, blank=True)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_depense', '-id']
        verbose_name = 'Dépense'
        verbose_name_plural = 'Dépenses'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.libelle}'


class DocumentVehicule(models.Model):
    """Document attaché à un véhicule (disponible ou à faire)."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='documents'
    )
    type_document = models.CharField('Type', max_length=80)
    numero = models.CharField('Numéro', max_length=60, blank=True)
    date_emission = models.DateField('Date émission', null=True, blank=True)
    date_echeance = models.DateField('Date échéance', null=True, blank=True)
    disponible = models.BooleanField('Disponible', default=False)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicule', 'type_document']
        verbose_name = 'Document véhicule'
        verbose_name_plural = 'Documents véhicule'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.type_document}'


class Reparation(models.Model):
    """Réparation effectuée ou à faire sur un véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='reparations'
    )
    date_reparation = models.DateField('Date', null=True, blank=True)
    kilometrage = models.PositiveIntegerField('Kilométrage', null=True, blank=True)
    type_rep = models.CharField('Type', max_length=60, blank=True)
    description = models.TextField('Description')
    cout = models.DecimalField(
        'Coût (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    prestataire = models.CharField('Prestataire', max_length=120, blank=True)
    a_faire = models.BooleanField('À faire', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_reparation', '-id']
        verbose_name = 'Réparation'
        verbose_name_plural = 'Réparations'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.description[:50]}'


class Location(models.Model):
    """Contrat de location (LLD, LOA, courte durée) avec CT, assurance, km vidange."""
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('a_venir', 'À venir'),
        ('termine', 'Terminé'),
    ]
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='locations'
    )
    locataire = models.CharField('Locataire', max_length=200)
    type_location = models.CharField(
        'Type', max_length=60
    )  # LLD, LOA, Location courte
    date_debut = models.DateField('Date début')
    date_fin = models.DateField('Date fin')
    loyer_mensuel = models.DecimalField(
        'Loyer mensuel (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    km_inclus_mois = models.PositiveIntegerField('Km inclus / mois', null=True, blank=True)
    prix_km_supplementaire = models.DecimalField(
        'Prix km supplémentaire (FCFA)', max_digits=10, decimal_places=0, null=True, blank=True
    )
    date_expiration_ct = models.DateField(
        'Date expiration visite technique (CT)', null=True, blank=True
    )
    date_expiration_assurance = models.DateField(
        'Date expiration assurance', null=True, blank=True
    )
    km_prochaine_vidange = models.PositiveIntegerField(
        'Kilométrage prochaine vidange', null=True, blank=True
    )
    remarques = models.TextField('Remarques', blank=True)
    statut = models.CharField(
        'Statut', max_length=20, choices=STATUT_CHOICES, default='en_cours'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def __str__(self):
        return f'{self.vehicule} — {self.locataire}'


class Vente(models.Model):
    """Vente / cession d'un véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='ventes'
    )
    date_vente = models.DateField('Date vente')
    acquereur = models.CharField('Acquéreur', max_length=200, blank=True)
    prix_vente = models.DecimalField(
        'Prix vente (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    km_vente = models.PositiveIntegerField('Km à la vente', null=True, blank=True)
    garantie_duree = models.CharField('Garantie', max_length=80, blank=True)
    etat_livraison = models.CharField('État livraison', max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_vente']
        verbose_name = 'Vente'
        verbose_name_plural = 'Ventes'

    def __str__(self):
        return f'{self.vehicule} — {self.date_vente}'


class Facture(models.Model):
    """Facture liée à un véhicule (achat, réparation, assurance, etc.)."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='factures'
    )
    numero = models.CharField('Numéro facture', max_length=80)
    fournisseur = models.CharField('Fournisseur', max_length=200, blank=True)
    date_facture = models.DateField('Date', null=True, blank=True)
    montant = models.DecimalField(
        'Montant (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    type_facture = models.CharField(
        'Type', max_length=60, blank=True,
        help_text='Ex: achat, réparation, assurance'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_facture', '-id']
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.numero}'


class ProfilUtilisateur(models.Model):
    """Profil étendu (rôle) pour les utilisateurs Django."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Gestionnaire'),
        ('user', 'Utilisateur'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_flotte'
    )
    role = models.CharField(
        'Rôle', max_length=20, choices=ROLE_CHOICES, default='user'
    )

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateur'

    def __str__(self):
        return f'{self.user.username} — {self.get_role_display()}'


class RapportJournalier(models.Model):
    """Rapport journalier ou document CA (PDF) déposé pour consultation."""
    TYPE_CHOICES = [
        ('journalier', 'Rapport journalier flotte'),
        ('ca', 'Document chiffre d\'affaires'),
        ('autre', 'Autre'),
    ]
    date_rapport = models.DateField('Date du rapport')
    titre = models.CharField('Titre', max_length=200)
    type_rapport = models.CharField(
        'Type', max_length=20, choices=TYPE_CHOICES, default='journalier'
    )
    fichier = models.FileField(
        'Fichier PDF', upload_to='rapports/%Y/%m/', max_length=255,
        help_text='Fichier PDF (rapport journalier, document CA)'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_rapport', '-id']
        verbose_name = 'Rapport journalier'
        verbose_name_plural = 'Rapports journaliers'

    def __str__(self):
        return f'{self.date_rapport} — {self.titre}'


class Maintenance(models.Model):
    """Maintenance préventive planifiée ou effectuée sur un véhicule."""
    TYPE_CHOICES = [
        ('vidange', 'Vidange'),
        ('courroie', 'Courroie de distribution'),
        ('pneus', 'Pneus'),
        ('filtres', 'Filtres (air, huile, habitacle)'),
        ('plaquettes', 'Plaquettes de frein'),
        ('batterie', 'Batterie'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('effectue', 'Effectué'),
    ]
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='maintenances'
    )
    type_maintenance = models.CharField(
        'Type', max_length=20, choices=TYPE_CHOICES, default='vidange'
    )
    date_prevue = models.DateField('Date prévue', null=True, blank=True)
    kilometrage_prevu = models.PositiveIntegerField(
        'Kilométrage prévu', null=True, blank=True
    )
    date_effectuee = models.DateField('Date effectuée', null=True, blank=True)
    kilometrage_effectue = models.PositiveIntegerField(
        'Kilométrage effectué', null=True, blank=True
    )
    cout = models.DecimalField(
        'Coût (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    prestataire = models.CharField('Prestataire', max_length=120, blank=True)
    statut = models.CharField(
        'Statut', max_length=20, choices=STATUT_CHOICES, default='a_faire'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_prevue', '-id']
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenances'

    def __str__(self):
        return f'{self.vehicule.libelle_court} — {self.get_type_maintenance_display()}'


class ReleveCarburant(models.Model):
    """Relevé de carburant (plein, consommation) par véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='releves_carburant'
    )
    date_releve = models.DateField('Date du relevé')
    kilometrage = models.PositiveIntegerField('Kilométrage')
    litres = models.DecimalField(
        'Litres', max_digits=8, decimal_places=2, null=True, blank=True
    )
    montant_fcfa = models.DecimalField(
        'Montant (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    prix_litre = models.DecimalField(
        'Prix au litre (FCFA)', max_digits=8, decimal_places=0, null=True, blank=True
    )
    lieu = models.CharField('Lieu (station)', max_length=120, blank=True)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_releve', '-id']
        verbose_name = 'Relevé carburant'
        verbose_name_plural = 'Relevés carburant'

    def __str__(self):
        return f'{self.vehicule.libelle_court} — {self.date_releve}'


class Conducteur(models.Model):
    """Conducteur (chauffeur) — peut être lié ou non à un utilisateur du système."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducteur_flotte'
    )
    nom = models.CharField('Nom', max_length=120)
    prenom = models.CharField('Prénom', max_length=120, blank=True)
    email = models.EmailField('Email', blank=True)
    telephone = models.CharField('Téléphone', max_length=30, blank=True)
    permis_numero = models.CharField('N° permis', max_length=60, blank=True)
    permis_date_expiration = models.DateField(
        'Date expiration permis', null=True, blank=True
    )
    actif = models.BooleanField('Actif', default=True)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = 'Conducteur'
        verbose_name_plural = 'Conducteurs'

    def __str__(self):
        if self.prenom:
            return f'{self.nom} {self.prenom}'
        return self.nom
