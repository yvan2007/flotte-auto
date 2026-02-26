"""
Modèles FLOTTE — Marques, modèles, types, véhicules (châssis = identifiant),
locations (CT, assurance, km vidange), import, dépenses, documents, réparations.
Tous les montants sont en FCFA.
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
    date_expiration_ct = models.DateField(
        'Date expiration CT (véhicule au parc)', null=True, blank=True,
        help_text='Pour véhicules non loués : prochaine échéance contrôle technique'
    )
    date_expiration_assurance = models.DateField(
        'Date expiration assurance (véhicule au parc)', null=True, blank=True,
        help_text='Pour véhicules non loués : échéance assurance'
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


class PhotoVehicule(models.Model):
    """Photo d'un véhicule sous différents angles."""
    ANGLE_CHOICES = [
        ('avant', 'Vue avant'),
        ('arriere', 'Vue arrière'),
        ('gauche', 'Vue côté gauche'),
        ('droit', 'Vue côté droit'),
        ('interieur_avant', 'Intérieur avant'),
        ('interieur_arriere', 'Intérieur arrière'),
        ('moteur', 'Moteur'),
        ('autre', 'Autre'),
    ]
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='photos'
    )
    photo = models.ImageField(
        'Photo', upload_to='vehicules_photos/%Y/%m/', max_length=255,
        help_text='Photo du véhicule (JPG, PNG)'
    )
    angle = models.CharField(
        'Angle / Vue', max_length=20, choices=ANGLE_CHOICES, default='autre',
        help_text='Angle de prise de vue'
    )
    description = models.CharField(
        'Description', max_length=200, blank=True,
        help_text='Description optionnelle de la photo'
    )
    est_principale = models.BooleanField(
        'Photo principale', default=False,
        help_text='Photo principale affichée en premier'
    )
    ordre = models.PositiveSmallIntegerField(
        'Ordre d\'affichage', default=0,
        help_text='Ordre d\'affichage (plus petit = affiché en premier)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vehicule', 'ordre', 'est_principale', '-created_at']
        verbose_name = 'Photo véhicule'
        verbose_name_plural = 'Photos véhicule'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.get_angle_display()}'


class ImportDemarche(models.Model):
    """Étape d'import / démarche par véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='import_demarches'
    )
    etape = models.CharField('Étape', max_length=80)
    date_etape = models.DateField('Date', null=True, blank=True)
    statut_etape = models.CharField('Statut étape', max_length=40, blank=True)
    fichier = models.FileField(
        'Pièce jointe (document)', upload_to='import_demarches/%Y/%m/', max_length=255,
        null=True, blank=True, help_text='Document scanné (PV, attestation, etc.)'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicule', 'id']
        verbose_name = 'Démarche import'
        verbose_name_plural = 'Démarches import'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.etape}'


class ChargeImport(models.Model):
    """Charges d'importation par véhicule : fret, dédouanement, transitaire, coût total (FCFA)."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='charges_import'
    )
    fret = models.DecimalField(
        'Fret (transport international, FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True
    )
    frais_dedouanement = models.DecimalField(
        'Frais de dédouanement (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True
    )
    frais_transitaire = models.DecimalField(
        'Frais de service du transitaire (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True
    )
    cout_total = models.DecimalField(
        'Coût total d\'importation (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text='Calcul automatique (fret + dédouanement + transitaire) ou saisie manuelle'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vehicule', '-id']
        verbose_name = 'Charge d\'importation'
        verbose_name_plural = 'Charges d\'importation'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — Import'

    def save(self, *args, **kwargs):
        from decimal import Decimal
        # Recalcul systématique : coût total = fret + dédouanement + transitaire (additions)
        if any(x is not None for x in (self.fret, self.frais_dedouanement, self.frais_transitaire)):
            total = (self.fret or Decimal(0)) + (self.frais_dedouanement or Decimal(0)) + (self.frais_transitaire or Decimal(0))
            self.cout_total = total
        super().save(*args, **kwargs)


class PartieImportee(models.Model):
    """Pièce ou partie de véhicule importée — coûts, quantités, association véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='parties_importees',
        help_text='Véhicule concerné (optionnel, pour stock général laisser vide)'
    )
    designation = models.CharField('Désignation', max_length=200)
    quantite = models.PositiveIntegerField('Quantité', default=1)
    cout_unitaire = models.DecimalField(
        'Coût unitaire (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicule', '-id']
        verbose_name = 'Partie importée'
        verbose_name_plural = 'Parties importées'

    def __str__(self):
        return f'{self.designation} — x{self.quantite}'

    @property
    def cout_total(self):
        if self.cout_unitaire is not None:
            return self.cout_unitaire * self.quantite
        return None


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


class TypeDocument(models.Model):
    """Type de document normalisé (carte grise, assurance, CT, vignette, etc.)."""
    libelle = models.CharField('Libellé', max_length=80, unique=True)
    ordre = models.PositiveSmallIntegerField('Ordre d\'affichage', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', 'libelle']
        verbose_name = 'Type de document'
        verbose_name_plural = 'Types de document'

    def __str__(self):
        return self.libelle


class DocumentVehicule(models.Model):
    """Document attaché à un véhicule (disponible ou à faire)."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='documents'
    )
    type_document_fk = models.ForeignKey(
        TypeDocument, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_vehicule', verbose_name='Type (liste)'
    )
    type_document = models.CharField('Type (libre si autre)', max_length=80, blank=True)
    numero = models.CharField('Numéro', max_length=60, blank=True)
    date_emission = models.DateField('Date émission', null=True, blank=True)
    date_echeance = models.DateField('Date échéance', null=True, blank=True)
    disponible = models.BooleanField('Disponible', default=False)
    fichier = models.FileField(
        'Fichier (document)', upload_to='documents_vehicule/%Y/%m/', max_length=255,
        null=True, blank=True, help_text='Document scanné (PDF, image)'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicule', 'type_document']
        verbose_name = 'Document véhicule'
        verbose_name_plural = 'Documents véhicule'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.libelle_type}'

    @property
    def libelle_type(self):
        """Type affiché : liste ou champ libre."""
        if self.type_document_fk_id:
            return self.type_document_fk.libelle
        return self.type_document or '—'


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
    conducteur = models.ForeignKey(
        'Conducteur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='locations', verbose_name='Conducteur assigné'
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
    cout_location = models.DecimalField(
        'Coût de location (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text='Coût global ou complément au loyer'
    )
    frais_annexes = models.DecimalField(
        'Frais annexes (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text='Assurance, entretien, carburant, etc.'
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

    @property
    def cout_total_location(self):
        """Coût total de la location (facture locataire) : loyer + frais annexes + contraventions à la charge du locataire."""
        from decimal import Decimal
        total = self.loyer_mensuel or Decimal(0)
        total += self.frais_annexes or Decimal(0)
        total += sum((c.montant or Decimal(0)) for c in self.contraventions.all())
        return total


class Contravention(models.Model):
    """Contravention / amende reçue pendant la location. Prise en charge par le locataire :
    le montant est automatiquement ajouté au coût total de la location (facture de location)."""
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name='contraventions'
    )
    date_contravention = models.DateField('Date', null=True, blank=True)
    motif = models.CharField(
        'Motif', max_length=200, blank=True,
        help_text='Ex: Excès de vitesse, Stationnement interdit, Non-respect de la signalisation'
    )
    reference = models.CharField('Référence / N° PV', max_length=80, blank=True)
    montant = models.DecimalField(
        'Montant (FCFA)', max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text='Montant à la charge du locataire, ajouté à la facture de location'
    )
    lieu = models.CharField('Lieu', max_length=120, blank=True)
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['location', '-date_contravention', '-id']
        verbose_name = 'Contravention'
        verbose_name_plural = 'Contraventions'

    def __str__(self):
        return f'{self.location} — {self.reference or self.date_contravention}'


class Vente(models.Model):
    """Vente / cession d'un véhicule."""
    vehicule = models.ForeignKey(
        Vehicule, on_delete=models.CASCADE, related_name='ventes'
    )
    date_vente = models.DateField('Date vente')
    acquereur = models.CharField('Acquéreur', max_length=200, blank=True)
    acquereur_compte = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventes_comme_acquereur',
        verbose_name='Compte client (acquéreur)',
        help_text='Si l\'acquéreur a un compte FLOTTE (rôle Utilisateur), associez-le pour qu\'il voie cette vente dans son espace.',
    )
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
    fichier = models.FileField(
        'Fichier (PDF)', upload_to='factures/%Y/%m/', max_length=255,
        null=True, blank=True, help_text='Facture scannée (PDF)'
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_facture', '-id']
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'

    def __str__(self):
        return f'{self.vehicule.numero_chassis} — {self.numero}'

    @property
    def total_avec_penalites(self):
        """Montant facture + somme des pénalités liées."""
        from decimal import Decimal
        base = self.montant or Decimal(0)
        penalites = sum((p.montant or Decimal(0)) for p in self.penalites.all())
        return base + penalites


class PenaliteFacture(models.Model):
    """Pénalité (retard, amende, etc.) liée à une facture."""
    facture = models.ForeignKey(
        Facture, on_delete=models.CASCADE, related_name='penalites'
    )
    date_penalite = models.DateField('Date', null=True, blank=True)
    libelle = models.CharField('Libellé', max_length=200, help_text='Ex: Retard de paiement, Amende')
    montant = models.DecimalField(
        'Montant (FCFA)', max_digits=14, decimal_places=0, null=True, blank=True
    )
    remarque = models.TextField('Remarque', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['facture', '-date_penalite', '-id']
        verbose_name = 'Pénalité facture'
        verbose_name_plural = 'Pénalités facture'

    def __str__(self):
        return f'{self.facture.numero} — {self.libelle}'


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

    # Code d'affichage des montants (chiffre d'affaires, etc.), stocké de façon hachée
    code_ca_hash = models.CharField(
        'Code affichage montants CA (haché)', max_length=128, blank=True
    )

    def set_code_ca(self, raw_code: str | None):
        """Définit ou réinitialise le code (4–8 chiffres recommandé)."""
        from django.contrib.auth.hashers import make_password

        raw_code = (raw_code or '').strip()
        if not raw_code:
            self.code_ca_hash = ''
        else:
            self.code_ca_hash = make_password(raw_code)

    def check_code_ca(self, raw_code: str | None) -> bool:
        """Vérifie le code saisi. Retourne False si aucun code défini."""
        from django.contrib.auth.hashers import check_password

        if not self.code_ca_hash:
            return False
        raw_code = (raw_code or '').strip()
        if not raw_code:
            return False
        return check_password(raw_code, self.code_ca_hash)


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

    def save(self, *args, **kwargs):
        from decimal import Decimal, ROUND_HALF_UP
        # Calcul automatique des montants liés : montant_fcfa = litres × prix_litre (ou compléter le champ manquant)
        litres = self.litres
        montant = self.montant_fcfa
        prix = self.prix_litre
        if litres is not None and prix is not None and prix != 0:
            if montant is None or montant == 0:
                self.montant_fcfa = (litres * prix).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        elif litres is not None and litres != 0 and montant is not None:
            if prix is None or prix == 0:
                self.prix_litre = (montant / litres).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        elif prix is not None and prix != 0 and montant is not None:
            if litres is None or litres == 0:
                self.litres = (montant / prix).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)


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


class AuditLog(models.Model):
    """Traçabilité des créations/modifications/suppressions sur les entités principales."""
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='+'
    )
    action = models.CharField('Action', max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField('Modèle', max_length=80)
    object_id = models.CharField('ID objet', max_length=50, blank=True)
    object_repr = models.CharField('Représentation', max_length=200, blank=True)
    timestamp = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Journal d\'audit'
        verbose_name_plural = 'Journaux d\'audit'

    def __str__(self):
        return f'{self.timestamp} — {self.get_action_display()} — {self.model_name} {self.object_id}'
