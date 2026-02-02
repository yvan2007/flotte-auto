"""
Remplit la base FLOTTE avec des données démo complètes : paramétrage, véhicules
(parc / import / vendu), import & démarches, dépenses, documents, réparations,
factures, locations, ventes, maintenance, carburant, conducteurs, utilisateurs.
Tous les cas et possibilités sont couverts.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

from flotte.models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, ImportDemarche, Depense, DocumentVehicule, Reparation,
    Location, Vente, Facture, ProfilUtilisateur, Maintenance,
    ReleveCarburant, Conducteur,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Remplit la base avec toutes les données démo (paramétrage, véhicules, dépenses, etc.).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprimer les données existantes avant de remplir (véhicules et liés, pas les users).',
        )
        parser.add_argument(
            '--no-param',
            action='store_true',
            help='Ne pas recharger le paramétrage (marques, modèles, types).',
        )

    def ensure_parametrage(self):
        """Charge le paramétrage initial si vide, puis retourne les listes."""
        if not TypeCarburant.objects.exists() and not self.no_param:
            call_command('load_parametrage_initial')
        elif TypeCarburant.objects.exists():
            self.stdout.write('Paramétrage déjà présent.')
        carburants = list(TypeCarburant.objects.all())
        transmissions = list(TypeTransmission.objects.all())
        types_veh = list(TypeVehicule.objects.all())
        marques = list(Marque.objects.all())
        modeles = list(Modele.objects.select_related('marque').all())
        return carburants, transmissions, types_veh, marques, modeles

    def ensure_users(self):
        """Crée les utilisateurs de test (user, gestion, yvan) avec profils."""
        users_created = []
        for username, password, role, is_super in [
            ('user', '52751040Ky', 'user', False),
            ('gestion', '52751040Ky', 'manager', False),
            ('yvan', '5275', 'admin', True),
        ]:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={'is_staff': is_super, 'is_superuser': is_super}
            )
            if created:
                u.set_password(password)
                u.save()
                users_created.append(username)
            p, _ = ProfilUtilisateur.objects.get_or_create(user=u, defaults={'role': role})
            if p.role != role:
                p.role = role
                p.save()
        if users_created:
            self.stdout.write(f'  Utilisateurs créés : {", ".join(users_created)}')
        self.stdout.write('  Utilisateurs (user, gestion, yvan) et profils OK.')

    def create_vehicules(self, marques, modeles, carburants, transmissions, types_veh):
        """Crée des véhicules : au parc, en import, vendus — tous les champs remplis."""
        if Vehicule.objects.exists() and not self.reset:
            self.stdout.write('Véhicules déjà présents (--reset pour tout supprimer).')
            return list(Vehicule.objects.all())

        if self.reset:
            self._reset_data()

        today = date.today()
        vehicules = []
        # Données variées : châssis, marque, modèle, année, statut, km, prix, etc.
        data = [
            ('CH001PARC001', 'parc', 'Mercedes', 'Classe C', 2022, 45000, 18500000, 'CI', 'Bon'),
            ('CH002PARC002', 'parc', 'Toyota', 'Corolla', 2023, 12000, 12500000, 'CI', 'Neuf'),
            ('CH003PARC003', 'parc', 'Renault', 'Clio', 2021, 78000, 6500000, 'France', 'Correct'),
            ('CH004IMPORT1', 'import', 'BMW', '320d', 2024, 0, 22000000, 'Allemagne', 'En attente'),
            ('CH005IMPORT2', 'import', 'Peugeot', '308', 2023, 500, 9800000, 'France', 'En transit'),
            ('CH006VEND001', 'vendu', 'VW', 'Golf', 2019, 95000, 7200000, 'Allemagne', 'Bon'),
            ('CH007VEND002', 'vendu', 'Renault', 'Mégane', 2018, 120000, 5500000, 'France', 'Usé'),
            ('CH008PARC004', 'parc', 'Audi', 'A4', 2022, 32000, 19500000, 'Allemagne', 'Très bon'),
            ('CH009PARC005', 'parc', 'Peugeot', '3008', 2023, 15000, 14500000, 'France', 'Neuf'),
            ('CH010PARC006', 'parc', 'Nissan', 'Qashqai', 2021, 52000, 11500000, 'Japon', 'Bon'),
            ('CH011PARC007', 'parc', 'Ford', 'Focus', 2020, 68000, 8500000, 'Belgique', 'Correct'),
            ('CH012PARC008', 'parc', 'Honda', 'Civic', 2022, 28000, 13200000, 'Japon', 'Très bon'),
            ('CH013PARC009', 'parc', 'Citroën', 'C3', 2021, 41000, 7200000, 'France', 'Bon'),
            ('CH014PARC010', 'parc', 'Renault', 'Kangoo', 2020, 89000, 6800000, 'France', 'Correct'),
        ]
        marques_d = {m.nom: m for m in marques}
        modeles_d = {}
        for mo in modeles:
            key = (mo.marque.nom, mo.nom)
            modeles_d[key] = mo

        for i, (chassis, statut, marque_nom, modele_nom, annee, km, prix, origine, etat) in enumerate(data):
            marque = marques_d.get(marque_nom)
            modele = modeles_d.get((marque_nom, modele_nom)) if marque else None
            tc = carburants[i % len(carburants)] if carburants else None
            tt = transmissions[i % len(transmissions)] if transmissions else None
            tv = types_veh[i % len(types_veh)] if types_veh else None
            v = Vehicule.objects.create(
                numero_chassis=chassis,
                marque=marque,
                modele=modele,
                annee=annee,
                type_vehicule=tv,
                type_carburant=tc,
                type_transmission=tt,
                couleur_exterieure=['Blanc', 'Noir', 'Gris', 'Bleu', 'Rouge', 'Argent'][i % 6],
                couleur_interieure=['Noir', 'Gris', 'Beige'][i % 3],
                date_entree_parc=today - timedelta(days=400 + i * 30),
                km_entree=max(0, km - (i * 1000)),
                kilometrage_actuel=max(0, km + (i * 500)),
                prix_achat=Decimal(str(prix)),
                origine_pays=origine,
                etat_entree=etat,
                statut=statut,
                numero_immatriculation=f'CI-{1234 + i}-AB' if statut != 'import' else '',
                date_premiere_immat=today - timedelta(days=500) if statut != 'import' else None,
                consommation_moyenne=Decimal('6.5') + (i % 3) * Decimal('0.5'),
                rejet_co2=120 + (i % 5) * 10,
                puissance_fiscale=6 + (i % 5),
                km_prochaine_vidange=(km + 10000) if statut == 'parc' else None,
            )
            vehicules.append(v)
        self.stdout.write(f'  {len(vehicules)} véhicules créés (parc, import, vendu).')
        return vehicules

    def _reset_data(self):
        """Supprime les données liées aux véhicules (ordre pour FK)."""
        for M in [ReleveCarburant, Maintenance, Vente, Location, Facture, Reparation,
                  DocumentVehicule, Depense, ImportDemarche]:
            n, _ = M.objects.all().delete()
            if n:
                self.stdout.write(f'  Supprimé {M.__name__}: {n} enregistrements.')
        Vehicule.objects.all().delete()
        Conducteur.objects.all().delete()
        self.stdout.write('  Véhicules et conducteurs supprimés.')

    def create_import_demarches(self, vehicules):
        """Démarches d'import pour véhicules en statut import."""
        import_veh = [v for v in vehicules if v.statut == 'import']
        etapes = [
            ('Commande fournisseur', 'en_cours'),
            ('Embarquement port', 'en_attente'),
            ('Transit maritime', 'en_cours'),
            ('Débarquement Abidjan', 'en_attente'),
            ('Dédouanement', 'en_attente'),
            ('Immatriculation', 'en_attente'),
        ]
        for v in import_veh:
            for j, (etape, statut) in enumerate(etapes):
                ImportDemarche.objects.get_or_create(
                    vehicule=v,
                    etape=etape,
                    defaults={
                        'date_etape': date.today() - timedelta(days=30 - j * 5),
                        'statut_etape': statut,
                        'remarque': f'Étape {j + 1}/6 pour {v.numero_chassis}',
                    }
                )
        n_import = ImportDemarche.objects.filter(vehicule__statut='import').count()
        self.stdout.write(f'  Démarches import : {n_import} créées pour {len(import_veh)} véhicules.')

    def create_depenses(self, vehicules):
        """Dépenses de tous types pour plusieurs véhicules."""
        types = ['entretien', 'reparation', 'carburant', 'assurance', 'autre']
        libelles = {
            'entretien': 'Vidange + filtres',
            'reparation': 'Remplacement plaquettes frein',
            'carburant': 'Plein carburant',
            'assurance': 'Assurance annuelle',
            'autre': 'Divers équipement',
        }
        montants = [45000, 120000, 38000, 250000, 15000]
        for v in vehicules[:10]:
            for i, typ in enumerate(types):
                Depense.objects.create(
                    vehicule=v,
                    type_depense=typ,
                    libelle=libelles[typ],
                    phase='Phase 1' if i % 2 == 0 else '',
                    montant=Decimal(str(montants[i] + (hash(v.numero_chassis) % 10000))),
                    date_depense=date.today() - timedelta(days=30 * (i + 1)),
                    remarque=f'Dépense {typ} pour {v.libelle_court}',
                )
        self.stdout.write(f'  Dépenses : {Depense.objects.count()} créées.')

    def create_documents(self, vehicules):
        """Documents véhicule : CT, assurance, carte grise, etc."""
        types_doc = [
            ('Carte grise', 'CG-2024-001', True),
            ('Contrôle technique', 'CT-2024-123', True),
            ('Assurance', 'ASS-2024-456', True),
            ('Permis de circulation', '', False),
        ]
        for v in vehicules[:12]:
            for typ, num, dispo in types_doc:
                DocumentVehicule.objects.get_or_create(
                    vehicule=v,
                    type_document=typ,
                    defaults={
                        'numero': num + f'-{v.id}' if num else '',
                        'date_emission': date.today() - timedelta(days=200),
                        'date_echeance': date.today() + timedelta(days=165),
                        'disponible': dispo,
                        'remarque': f'Document {typ}',
                    }
                )
        self.stdout.write(f'  Documents véhicule : {DocumentVehicule.objects.count()} créés.')

    def create_reparations(self, vehicules):
        """Réparations effectuées et à faire."""
        for v in vehicules[:10]:
            Reparation.objects.create(
                vehicule=v,
                date_reparation=date.today() - timedelta(days=60),
                kilometrage=max(0, (v.kilometrage_actuel or 0) - 2000),
                type_rep='Freinage',
                description='Remplacement plaquettes et disques avant',
                cout=Decimal('185000'),
                prestataire='Garage Central',
                a_faire=False,
            )
            Reparation.objects.create(
                vehicule=v,
                date_reparation=None,
                kilometrage=None,
                type_rep='Distribution',
                description='Changement courroie de distribution à prévoir',
                cout=Decimal('320000'),
                prestataire='',
                a_faire=True,
            )
        self.stdout.write(f'  Réparations : {Reparation.objects.count()} créées.')

    def create_factures(self, vehicules):
        """Factures (achat, réparation, assurance)."""
        for v in vehicules[:10]:
            for typ, num_prefix, mont in [('achat', 'FAC-ACH-', v.prix_achat or 0), ('réparation', 'FAC-REP-', 185000), ('assurance', 'FAC-ASS-', 250000)]:
                Facture.objects.create(
                    vehicule=v,
                    numero=f'{num_prefix}{v.id}-2024',
                    fournisseur='Fournisseur FLOTTE' if typ == 'achat' else 'Garage / Assureur',
                    date_facture=date.today() - timedelta(days=100),
                    montant=Decimal(str(mont)),
                    type_facture=typ,
                    remarque=f'Facture {typ}',
                )
        self.stdout.write(f'  Factures : {Facture.objects.count()} créées.')

    def create_locations(self, vehicules):
        """Locations : en cours, à venir, terminées."""
        parc_veh = [v for v in vehicules if v.statut == 'parc']
        for i, v in enumerate(parc_veh[:6]):
            statut = ['en_cours', 'en_cours', 'a_venir', 'termine', 'en_cours', 'termine'][i % 6]
            d_end = date.today() + timedelta(days=90) if statut in ('en_cours', 'a_venir') else date.today() - timedelta(days=30)
            d_start = date.today() - timedelta(days=180) if statut == 'en_cours' else (date.today() + timedelta(days=10) if statut == 'a_venir' else date.today() - timedelta(days=400))
            Location.objects.create(
                vehicule=v,
                locataire=f'Société Locataire {i + 1}',
                type_location='LLD' if i % 2 == 0 else 'LOA',
                date_debut=d_start,
                date_fin=d_end,
                loyer_mensuel=Decimal('450000') + i * 50000,
                km_inclus_mois=1500,
                prix_km_supplementaire=Decimal('75'),
                date_expiration_ct=date.today() + timedelta(days=120),
                date_expiration_assurance=date.today() + timedelta(days=200),
                km_prochaine_vidange=(v.kilometrage_actuel or 0) + 10000,
                remarques=f'Location {statut}',
                statut=statut,
            )
        self.stdout.write(f'  Locations : {Location.objects.count()} créées.')

    def create_ventes(self, vehicules):
        """Ventes pour véhicules vendus."""
        vendus = [v for v in vehicules if v.statut == 'vendu']
        for i, v in enumerate(vendus):
            Vente.objects.create(
                vehicule=v,
                date_vente=date.today() - timedelta(days=60 + i * 30),
                acquereur=f'Client / Entreprise {i + 1}',
                prix_vente=(v.prix_achat or Decimal('0')) * Decimal('0.85'),
                km_vente=v.kilometrage_actuel,
                garantie_duree='3 mois',
                etat_livraison='Conforme',
            )
        self.stdout.write(f'  Ventes : {Vente.objects.count()} créées.')

    def create_maintenances(self, vehicules):
        """Maintenances : à faire, en cours, effectuées — tous types."""
        types = ['vidange', 'courroie', 'pneus', 'filtres', 'plaquettes', 'batterie', 'autre']
        statuts = ['a_faire', 'en_cours', 'effectue', 'effectue', 'a_faire', 'effectue', 'a_faire']
        for v in vehicules[:12]:
            for j, (typ, statut) in enumerate(zip(types, statuts)):
                km = (v.kilometrage_actuel or 0) + 5000 + j * 2000
                Maintenance.objects.create(
                    vehicule=v,
                    type_maintenance=typ,
                    date_prevue=date.today() + timedelta(days=30 * (j + 1)),
                    kilometrage_prevu=km,
                    date_effectuee=date.today() - timedelta(days=20) if statut == 'effectue' else None,
                    kilometrage_effectue=max(0, km - 1000) if statut == 'effectue' else None,
                    cout=Decimal('45000') + j * 15000,
                    prestataire='Garage FLOTTE',
                    statut=statut,
                    remarque=f'Maintenance {typ}',
                )
        self.stdout.write(f'  Maintenances : {Maintenance.objects.count()} créées.')

    def create_releves_carburant(self, vehicules):
        """Relevés carburant pour véhicules au parc."""
        parc = [v for v in vehicules if v.statut == 'parc']
        for v in parc[:10]:
            for j in range(3):
                d = date.today() - timedelta(days=15 * (j + 1))
                km = (v.kilometrage_actuel or 0) - (j + 1) * 1500
                ReleveCarburant.objects.create(
                    vehicule=v,
                    date_releve=d,
                    kilometrage=max(0, km),
                    litres=Decimal('45.5') + j * 2,
                    montant_fcfa=Decimal('35000') + j * 5000,
                    prix_litre=Decimal('750'),
                    lieu='Station Total Abidjan',
                    remarque=f'Relevé {d}',
                )
        self.stdout.write(f'  Relevés carburant : {ReleveCarburant.objects.count()} créés.')

    def create_conducteurs(self):
        """Conducteurs actifs et inactifs."""
        if Conducteur.objects.exists():
            self.stdout.write('  Conducteurs déjà présents.')
            return
        data = [
            ('Koné', 'Amadou', True, 'PERM-2020-001'),
            ('Ouattara', 'Fatou', True, 'PERM-2019-002'),
            ('Diallo', 'Moussa', False, 'PERM-2018-003'),
            ('Bamba', 'Aïcha', True, 'PERM-2021-004'),
            ('Traoré', 'Ibrahim', True, 'PERM-2022-005'),
            ('Coulibaly', 'Mariam', True, 'PERM-2020-006'),
        ]
        for nom, prenom, actif, permis in data:
            Conducteur.objects.create(
                nom=nom,
                prenom=prenom,
                email=f'{prenom.lower()}.{nom.lower()}@flotte.ci',
                telephone=f'07 0{len(nom)} 12 34 56',
                permis_numero=permis,
                permis_date_expiration=date.today() + timedelta(days=400),
                actif=actif,
                remarque='Conducteur démo',
            )
        self.stdout.write(f'  Conducteurs : {Conducteur.objects.count()} créés.')

    def handle(self, *args, **options):
        self.reset = options.get('reset', False)
        self.no_param = options.get('no_param', False)
        self.stdout.write('Remplissage base FLOTTE (données démo complètes)...')

        carburants, transmissions, types_veh, marques, modeles = self.ensure_parametrage()
        if not marques:
            marques = list(Marque.objects.all())
            modeles = list(Modele.objects.select_related('marque').all())
            carburants = list(TypeCarburant.objects.all())
            transmissions = list(TypeTransmission.objects.all())
            types_veh = list(TypeVehicule.objects.all())

        self.ensure_users()
        vehicules = self.create_vehicules(marques, modeles, carburants, transmissions, types_veh)
        if vehicules is None:
            vehicules = list(Vehicule.objects.all())

        self.create_import_demarches(vehicules)
        self.create_depenses(vehicules)
        self.create_documents(vehicules)
        self.create_reparations(vehicules)
        self.create_factures(vehicules)
        self.create_locations(vehicules)
        self.create_ventes(vehicules)
        self.create_maintenances(vehicules)
        self.create_releves_carburant(vehicules)
        self.create_conducteurs()

        self.stdout.write(self.style.SUCCESS('Base remplie avec succès.'))
