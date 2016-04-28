from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from os import path
import csv
from django.contrib.auth.models import User
from DRP.models import LabGroup, Compound, PerformedReaction
from DRP.models import ChemicalClass, NumRxnDescriptor
from DRP.models import BoolRxnDescriptor, OrdRxnDescriptor
from DRP.models import NumRxnDescriptorValue, BoolRxnDescriptorValue
from DRP.models import OrdRxnDescriptorValue, NumMolDescriptorValue
from DRP.models import CompoundRole, CompoundQuantity
from chemspipy import ChemSpider

outcomeDescriptor = OrdRxnDescriptor.objects.get_or_create(
    heading='crystallisation_outcome',
    name='Four class crystallisation outcome',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0',
    maximum=4,
    minimum=1
    )[0]

outcomeBooleanDescriptor = BoolRxnDescriptor.objects.get_or_create(
    heading='boolean_crystallisation_outcome',
    name='Two class crystallisation outcome',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

purityDescriptor = OrdRxnDescriptor.objects.get_or_create(
    heading='crystallisation_purity_outcome',
    name='Two class crystallisation purity',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0',
    maximum=2,
    minimum=1
    )[0]

temperatureDescriptor = NumRxnDescriptor.objects.get_or_create(
    heading='reaction_temperature',
    name='Reaction temperature in degrees C',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

timeDescriptor = NumRxnDescriptor.objects.get_or_create(
    heading='reaction_time',
    name='Reaction time in minutes',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

pHDescriptor = NumRxnDescriptor.objects.get_or_create(
    heading='reaction_pH',
    name='Reaction pH',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

preHeatStandingDescriptor = NumRxnDescriptor.objects.get_or_create(
    heading='pre_heat_standing',
    name='Pre heat standing time',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

teflonDescriptor = BoolRxnDescriptor.objects.get_or_create(
    heading='teflon_pouch',
    name='Was this reaction performed in a teflon pouch?',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

leakDescriptor = BoolRxnDescriptor.objects.get_or_create(
    heading='leak',
    name='Did this reaction leak?',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

slowCoolDescriptor = BoolRxnDescriptor.objects.get_or_create(
    heading='slow_cool',
    name='Was a slow cool performed for this reaction?',
    calculatorSoftware='manual',
    calculatorSoftwareVersion='0'
    )[0]

# about how many things django can bulk_create at once without getting upset
save_at_once = 50


class Command(BaseCommand):
    help = 'Ports database from pre-0.02 to 0.02'

    def add_arguments(self, parser):
        parser.add_argument('directory', help='The directory where the tsv files are')
        parser.add_argument('start_number', type=int, nargs='?', default=0, help='Number to start on. By default this specifies a reaction. If descriptors or quantities is specified it refers to those.')
        parser.add_argument('--descriptors', action='store_true', help='Start at importing the descriptors')
        parser.add_argument('--quantities', action='store_true', help='Start at importing the compound quantities')

    def handle(self, *args, **kwargs):
        folder = kwargs['directory']
        start_at_descriptors = kwargs['descriptors']
        start_at_quantities = kwargs['quantities']
        start_number = kwargs['start_number']
        if start_at_descriptors and start_at_quantities:
            raise RuntimeError('Only one of descriptors and quantities is allowed to be specified')
        start_at_reactions = not (start_at_descriptors or start_at_quantities)

        if not path.isfile(path.join(folder, 'performedReactionsNoDupsLower.tsv')):
            self.stdout.write('Writing file with all references that were uppercase (now lower) and duplicate references disambiguated (arbitrarily)')
            with open(path.join(folder, 'performedReactions.tsv')) as in_file, open(path.join(folder, 'performedReactionsNoDupsLower.tsv'), 'w') as out_file:
                references = set()
                reader = csv.DictReader(in_file, delimiter='\t')
                writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=reader.fieldnames)
                writer.writeheader()

                case_count = 0
                valid_case_count = 0
                dup_count = 0
                for r in reader:
                    ref = r['reference'].lower()
                    new_ref = ref
                    if ref in references:
                        dup_count += 1
                        i = 1
                        while new_ref in references:
                            new_ref = '{}_dup{}'.format(ref, i)
                            i += 1
                        self.stderr.write('Reference {} duplicated {} times. Renamed and invalidated'.format(ref, i))
                    references.add(new_ref)
                    r['reference'] = str(new_ref)
                    writer.writerow(r)
            self.stderr.write('{} references with _dupX appended to remove duplicate reference'.format(dup_count))
        if start_at_reactions:
            with open(path.join(folder, 'performedReactionsNoDupsLower.tsv')) as reactions:
                self.stdout.write('Adding or updating reactions')
                reader = csv.DictReader(reactions, delimiter='\t')
                for i, r in enumerate(reader):
                    if start_at_reactions and i < start_number:
                        continue
                    ref = r['reference'].lower()
                    if '_dup' in ref:
                        base_ref = ref.split('_dup')[0]
                        PerformedReaction.objects.filter(reference=base_ref).update(valid=False)
                        valid = False
                    else:
                        valid = bool(int(r['valid']))
                    ps = PerformedReaction.objects.filter(reference=ref)
                    if ps.exists():
                        if ps.count() > 1:
                            raise RuntimeError('More than one reaction with reference {}'.fromat(ref))
                        self.stdout.write('{}: Updating reaction with reference {}'.format(i, ref))

                        ps.update(labGroup=LabGroup.objects.get(title=r['labGroup.title']),
                                    notes=r['notes'],
                                    user=User.objects.get(username=r['user.username']),
                                    valid=valid,
                                    legacyRecommendedFlag=(r['legacyRecommendedFlag'] == 'Yes'),
                                    insertedDateTime=r['insertedDateTime'],
                                    public=int(r['public'])
                                  )
                    else:
                        p = PerformedReaction(
                            reference=ref,
                            labGroup=LabGroup.objects.get(title=r['labGroup.title']),
                            notes=r['notes'],
                            user=User.objects.get(username=r['user.username']),
                            valid=int(r['valid']),
                            legacyRecommendedFlag=(r['legacyRecommendedFlag'] == 'Yes'),
                            insertedDateTime=r['insertedDateTime'],
                            public=int(r['public'])
                            )
                        self.stdout.write('{}: Creating reaction with reference {}'.format(i, ref))
                        p.validate_unique()
                        p.save(calcDescriptors=False)
        if not start_at_quantities:
            with open(path.join(folder, 'performedReactionsNoDupsLower.tsv')) as reactions:
                self.stdout.write('Creating manual descriptors')
                reader = csv.DictReader(reactions, delimiter='\t')
                outValues = []
                outBoolValues = []
                purityValues = []
                temperatureValues = []
                timeValues = []
                pHValues = []
                preHeatStandingValues = []
                teflonValues = []
                slowCoolValues = []
                leakValues = []



                for i, r in enumerate(reader):
                    if start_at_descriptors and i < start_number:
                        continue
                    ref = r['reference'].lower()
                    self.stdout.write('{}: Reiterating for reaction with reference {}'.format(i, ref))
                    ps = PerformedReaction.objects.filter(reference=ref)
                    if not ps:
                        raise RuntimeError('Cannot find reaction with reference {}'.format(ref))
                    else:
                        if ps.count() > 1:
                            raise RuntimeError('More than one reaction with reference {}'.format(ref))
                        p = ps[0]
                        try:
                            p.duplicateOf = PerformedReaction.objects.get(reference=r['duplicateOf.reference'].lower())
                            p.save(calcDescriptors=False)
                        except PerformedReaction.DoesNotExist:
                            pass

                        outcomeValue = int(r['outcome']) if (r['outcome'] in (str(x) for x in range (1, 5))) else None
                        try:
                            v = OrdRxnDescriptorValue.objects.get(descriptor=outcomeDescriptor, reaction=p)
                            if v.value != outcomeValue:
                                v.value = outcomeValue
                                v.save()
                        except OrdRxnDescriptorValue.DoesNotExist:
                            outValue = outcomeDescriptor.createValue(p, outcomeValue)
                            outValues.append(outValue)

                        value = True if (outcomeValue > 2) else False
                        try:
                            v = BoolRxnDescriptorValue.objects.get(descriptor=outcomeBooleanDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except BoolRxnDescriptorValue.DoesNotExist:
                            outBoolValue = outcomeBooleanDescriptor.createValue(p, value)
                            outBoolValues.append(outBoolValue)

                        value = int(r['purity']) if (r['purity'] in ('1', '2')) else None
                        try:
                            v = OrdRxnDescriptorValue.objects.get(descriptor=purityDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except OrdRxnDescriptorValue.DoesNotExist:
                            purityValue = purityDescriptor.createValue(p, value)
                            purityValues.append(purityValue)

                        value = (float(r['temp']) + 273.15) if (r['temp'] not in ('', '?')) else None
                        try:
                            v = NumRxnDescriptorValue.objects.get(descriptor=temperatureDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except NumRxnDescriptorValue.DoesNotExist:
                            temperatureDescriptorValue = temperatureDescriptor.createValue(p, value)
                            temperatureValues.append(temperatureDescriptorValue)

                        value = float(r['time'])*60 if (r['time'] not in ['', '?']) else None
                        try:
                            v = NumRxnDescriptorValue.objects.get(descriptor=timeDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except NumRxnDescriptorValue.DoesNotExist:
                            timeDescriptorValue = timeDescriptor.createValue(p, value)
                            timeValues.append(timeDescriptorValue)

                        value = float(r['pH']) if (r['pH'] not in ('', '?')) else None
                        try:
                            v = NumRxnDescriptorValue.objects.get(descriptor=pHDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except NumRxnDescriptorValue.DoesNotExist:
                            pHDescriptorValue = pHDescriptor.createValue(p, value)
                            pHValues.append(pHDescriptorValue)

                        value = bool(r['pre_heat standing']) if (r.get('pre_heat standing') not in ('', None)) else None
                        try:
                            v = NumRxnDescriptorValue.objects.get(descriptor=preHeatStandingDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except NumRxnDescriptorValue.DoesNotExist:
                            preHeatStandingDescriptorValue = preHeatStandingDescriptor.createValue(p, value)
                            preHeatStandingValues.append(preHeatStandingDescriptorValue)

                        value = bool(int(r['teflon_pouch'])) if (r.get('teflon_pouch') not in(None, '')) else None
                        try:
                            v = BoolRxnDescriptorValue.objects.get(descriptor=teflonDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except BoolRxnDescriptorValue.DoesNotExist:
                            teflonDescriptorValue = teflonDescriptor.createValue(p, value)
                            teflonValues.append(teflonDescriptorValue)

                        leak_string = r['leak']
                        if leak_string in (None, '', '?'):
                            value = None
                        elif leak_string.lower() == 'yes':
                            value = True
                        elif leak_string.lower() == 'no':
                            value = False
                        else:
                            raise RuntimeError("Unrecognized string '{}' in leak column".format(leak_string))
                        try:
                            v = BoolRxnDescriptorValue.objects.get(descriptor=leakDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except BoolRxnDescriptorValue.DoesNotExist:
                            leakDescriptorValue = leakDescriptor.createValue(p, value)
                            leakValues.append(leakDescriptorValue)

                        slow_cool_string = r['slow_cool']
                        if slow_cool_string in (None, '', '?'):
                            value = None
                        elif slow_cool_string.lower() == 'yes':
                            value = True
                        elif slow_cool_string.lower() == 'no':
                            value = False
                        else:
                            raise RuntimeError("Unrecognized string '{}' in slow_cool column".format(slow_cool_string))
                        try:
                            v = BoolRxnDescriptorValue.objects.get(descriptor=slowCoolDescriptor, reaction=p)
                            if v.value != value:
                                v.value = value
                                v.save()
                        except BoolRxnDescriptorValue.DoesNotExist:
                            slowCoolDescriptorValue = slowCoolDescriptor.createValue(p, value)
                            slowCoolValues.append(slowCoolDescriptorValue)

                        if len(outValues) > save_at_once:
                            self.stdout.write("Saving outValues...")
                            OrdRxnDescriptorValue.objects.bulk_create(outValues)
                            outValues = []
                            self.stdout.write("...saved")
                        if len(outBoolValues) > save_at_once:
                            self.stdout.write("Saving outBoolValues...")
                            BoolRxnDescriptorValue.objects.bulk_create(outBoolValues)
                            outBoolValues = []
                            self.stdout.write("...saved")
                        if len(purityValues) > save_at_once:
                            self.stdout.write("Saving purityValues...")
                            OrdRxnDescriptorValue.objects.bulk_create(purityValues)
                            purityValues = []
                            self.stdout.write("...saved")
                        if len(temperatureValues) > save_at_once:
                            self.stdout.write("Saving temperatureValues...")
                            NumRxnDescriptorValue.objects.bulk_create(temperatureValues)
                            temperatureValues = []
                            self.stdout.write("...saved")
                        if len(timeValues) > save_at_once:
                            self.stdout.write("Saving timeValues...")
                            NumRxnDescriptorValue.objects.bulk_create(timeValues)
                            timeValues = []
                            self.stdout.write("...saved")
                        if len(pHValues) > save_at_once:
                            self.stdout.write("Saving pHValues...")
                            NumRxnDescriptorValue.objects.bulk_create(pHValues)
                            pHValues = []
                            self.stdout.write("...saved")
                        if len(preHeatStandingValues) > save_at_once:
                            self.stdout.write("Saving preHeatStandingValues...")
                            NumRxnDescriptorValue.objects.bulk_create(preHeatStandingValues)
                            preHeatStandingValues = []
                            self.stdout.write("...saved")
                        if len(teflonValues) > save_at_once:
                            self.stdout.write("Saving teflonValues...")
                            BoolRxnDescriptorValue.objects.bulk_create(teflonValues)
                            teflonValues = []
                            self.stdout.write("...saved")
                        if len(leakValues) > save_at_once:
                            self.stdout.write("Saving leakValues...")
                            BoolRxnDescriptorValue.objects.bulk_create(leakValues)
                            leakValues = []
                            self.stdout.write("...saved")
                        if len(slowCoolValues) > save_at_once:
                            self.stdout.write("Saving slowCoolValues...")
                            BoolRxnDescriptorValue.objects.bulk_create(slowCoolValues)
                            slowCoolValues = []
                            self.stdout.write("...saved")

                self.stdout.write("Saving all remaining values...")
                OrdRxnDescriptorValue.objects.bulk_create(outValues)
                BoolRxnDescriptorValue.objects.bulk_create(outBoolValues)
                OrdRxnDescriptorValue.objects.bulk_create(purityValues)
                NumRxnDescriptorValue.objects.bulk_create(temperatureValues)
                NumRxnDescriptorValue.objects.bulk_create(timeValues)
                NumRxnDescriptorValue.objects.bulk_create(pHValues)
                NumRxnDescriptorValue.objects.bulk_create(preHeatStandingValues)
                BoolRxnDescriptorValue.objects.bulk_create(teflonValues)
                BoolRxnDescriptorValue.objects.bulk_create(leakValues)
                BoolRxnDescriptorValue.objects.bulk_create(slowCoolValues)


                outValues = []
                outBoolValues = []
                purityValues = []
                temperatureValues = []
                timeValues = []
                pHValues = []
                preHeatStandingValues = []
                teflonValues = []
                leakValues = []
                slowCoolValues = []
                self.stdout.write("...saved")

        with open(path.join(folder, 'compoundquantities.tsv')) as cqs:
            self.stdout.write('Creating or updating compound quantities')
            reader = csv.DictReader(cqs, delimiter='\t')
            quantities = []
            for i, r in enumerate(reader):
                if start_at_quantities and (i < start_number):
                    continue
                try:
                    reaction = PerformedReaction.objects.get(reference=r['reaction.reference'].lower())
                    compound = Compound.objects.get(abbrev=r['compound.abbrev'], labGroup=reaction.labGroup)
                    self.stdout.write('{}: Adding or updating quantity for compound {} and reaction {}'.format(i, reaction.reference, compound.abbrev))
                    if r['compound.abbrev'] in ('water', 'H2O'):
                        r['density'] = 1
                    mw = NumMolDescriptorValue.objects.get(compound=compound, descriptor__heading='mw').value
                    if r['compoundrole.name'] in (None, '', '?'):
                        self.stderr.write('No role for reactant {} with amount {} {} in reaction {}'.format(r['compound.abbrev'], r['amount'], r['unit'], r['reaction.reference']))
                        reaction.notes += ' No role for reactant {} with amount {} {}'.format(r['compound.abbrev'], r['amount'], r['unit'])
                        reaction.save(calcDescriptors=False)
                    elif r['compoundrole.name'] == 'pH':
                        reaction.notes += ' pH adjusting reagent used: {}, {}{}'.format(r['compound.abbrev'], r['amount'], r['unit'])
                        reaction.save(calcDescriptors=False)
                    else:
                        self.stdout.write('adding {} to {}'.format(compound.abbrev, reaction.reference))
                        compoundrole = CompoundRole.objects.get_or_create(label=r['compoundrole.name'])[0]
                        if r['amount'] in ('', '?'):
                            amount = None
                            reaction.notes += ' No amount for reactant {} with role {}'.format(r['compound.abbrev'], r['compoundrole.name'])
                        elif r['unit'] == 'g':
                            amount = float(r['amount'])/mw
                        elif r['unit'] == 'd':
                            amount = float(r['amount'])*0.0375*float(r['density'])/mw
                        elif r['unit'] == 'mL':
                            amount = float(r['amount'])*float(r['density'])/mw
                        else:
                            raise RuntimeError('invalid unit entered')
                        # convert to millimoles
                        if amount is not None:
                            amount = (amount * 1000)
                        cqq = CompoundQuantity.objects.filter(compound=compound, reaction=reaction)
                        if cqq.count() > 1:
                            cqq.delete()
                        try:
                            quantity = CompoundQuantity.objects.get(compound=compound, reaction=reaction)
                            if quantity.amount != amount or quantity.role != compoundrole:
                                quantity.amount = amount
                                quantity.role = compoundrole
                        except CompoundQuantity.DoesNotExist:
                            quantity = CompoundQuantity(compound=compound, reaction=reaction, role=compoundrole)
                            quantities.append(quantity)

                        # about how many things django can bulk_create at once without getting upset
                        if len(quantities) > save_at_once:
                            CompoundQuantity.objects.bulk_create(quantities)
                            quantities = []

                except Compound.DoesNotExist as e:
                    self.stderr.write('Unknown Reactant {} with amount {} {} in reaction {}'.format(r['compound.abbrev'], r['amount'], r['unit'], r['reaction.reference']))
                    reaction.notes += ('Unknown Reactant {} with amount {} {}'.format(r['compound.abbrev'], r['amount'], r['unit']))
                    reaction.save()
                    reaction.notes += ' Unknown Reactant {} with amount {} {}'.format(r['compound.abbrev'], r['amount'], r['unit'])
                    reaction.valid = False
                    reaction.save(calcDescriptors=False)
                except PerformedReaction.DoesNotExist as e:
                    self.stderr.write('Cannot find reactions {}'.format(r['reaction.reference']))
                    raise e

            CompoundQuantity.objects.bulk_create(quantities)
            quantities = []