#!/usr/bin/env python

from django.conf import settings
from HttpTest import GetHttpTest, PostHttpTest, GetHttpSessionTest, PostHttpSessionTest
from HttpTest import redirectionMixinFactory, logsInAs, usesCsrf
from HttpTest import choosesLabGroup
from DRP.tests.decorators import joinsLabGroup, createsChemicalClass, signsExampleLicense
from DRP.tests.decorators import createsUser, createsCompound, createsPerformedReaction
from DRP.tests.decorators import createsOrdRxnDescriptor, loadsCompoundsFromCsv
from DRP.tests.decorators import createsCompoundRole, createsCompoundQuantity
from DRP.tests.decorators import createsOrdRxnDescriptorValue
from DRP.tests import runTests
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import requests
import unittest
from DRP.models import LabGroup, CompoundRole, Compound, PerformedReaction
from DRP.models import CompoundQuantity, OrdRxnDescriptor, OrdRxnDescriptorValue
from urllib import urlencode

loadTests = unittest.TestLoader().loadTestsFromTestCase

newReactionUrl = GetHttpTest.url + reverse('newReaction')
reactionBaseCodes = ['ea5108a2-0b88-482d-90c5-ea492fd8134e', '823d22e7-3337-4292-aa67-13f748b2aa65', '1f47e7ab-1900-4683-ba1c-63330ec2f71a']


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
class GetReactionCreate(GetHttpSessionTest):

    url = newReactionUrl
    testCodes = ['6813e404-f1a3-48ed-ae97-600a41cf63cb', '2758c44c-b7e2-440a-a617-36d9d730bc93'] + reactionBaseCodes


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@usesCsrf
class PostReactionCreateValid(PostHttpSessionTest, redirectionMixinFactory(1)):  # effectively tests GET for add_reactants view

    url = newReactionUrl
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _payload = {'reference': 'turkish_delight'}

    def setUp(self):
        self.payload['labGroup'] = LabGroup.objects.get(title='narnia').id
        super(PostReactionCreateValid, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@usesCsrf
class PostReactionCreateInvalid(PostHttpSessionTest):

    url = newReactionUrl
    testCodes = ['6813e404-f1a3-48ed-ae97-600a41cf63cb', '2758c44c-b7e2-440a-a617-36d9d730bc93'] + reactionBaseCodes
    _payload = {'reference': ''}

    def setUp(self):
        self.payload['labGroup'] = LabGroup.objects.get(title='narnia').id
        super(PostReactionCreateInvalid, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
class GetReactionEdit(GetHttpSessionTest):

    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06', '2758c44c-b7e2-440a-a617-36d9d730bc93'] + reactionBaseCodes

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').id})
        super(GetReactionEdit, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
class GetReactionEdit2(GetHttpSessionTest):

    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06', '634d88bb-9289-448b-a3dc-548ff4c6cda1', '2758c44c-b7e2-440a-a617-36d9d730bc93'] + reactionBaseCodes

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').id})
        super(GetReactionEdit2, self).setUp()


@logsInAs('Aslan', 'old_magic')
@createsUser('WhiteQueen', 'New Magic')
@signsExampleLicense('Aslan')
@signsExampleLicense('WhiteQueen')
@joinsLabGroup('Aslan', 'narnia')
@joinsLabGroup('WhiteQueen', 'WhiteQueensArmy')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsPerformedReaction('WhiteQueensArmy', 'WhiteQueen', 'turkish_delight')
class GetSomeoneElsesReactionEdit(GetHttpSessionTest):
    '''Attempts to grab someone else\'s reaction, which should fail with a 404.'''

    status = 404

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='WhiteQueensArmy').id})
        super(GetSomeoneElsesReactionEdit, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
class GetNonexistentReactionEdit(GetHttpSessionTest):

    status = 404

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': 4})
        super(GetNonexistentReactionEdit, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@usesCsrf
class PostReactionEditValid(PostHttpSessionTest):

    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06', '2758c44c-b7e2-440a-a617-36d9d730bc93', 'd96fc7a1-69cf-44ac-975d-a67f9e2c74d0'] + reactionBaseCodes

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').id})
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia')
        self.payload.update({'notes': 'this reaction has been edited', 'reference': self.reaction.reference, 'labGroup': self.reaction.labGroup.id, 'performedBy': self.reaction.user.id, 'performedDateTime': self.reaction.performedDateTime, 'valid': self.reaction.valid, 'duplicateOf': ""})
        super(PostReactionEditValid, self).setUp()

    def test_edit(self):
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia')
        self.assertEqual(self.reaction.notes, 'this reaction has been edited')


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@usesCsrf
class PostReactionEditInvalid(PostHttpSessionTest):

    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06', '2758c44c-b7e2-440a-a617-36d9d730bc93'] + reactionBaseCodes

    def setUp(self):
        self.url = self.url + reverse('editReaction', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').id})
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia')
        self.payload.update({'notes': 'this reaction has been edited', 'labGroup': self.reaction.labGroup.id, 'performedBy': self.reaction.user.id, 'performedDateTime': self.reaction.performedDateTime, 'valid': self.reaction.valid, 'duplicateOf': ""})
        super(PostReactionEditInvalid, self).setUp()

    def test_edit(self):
        self.assertNotEqual(self.reaction.notes, 'this reaction has been edited')


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@usesCsrf
class DeletePerformedReaction(PostHttpSessionTest, redirectionMixinFactory(1)):

    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes

    def setUp(self):
        self.url = self.url + reverse('deleteReaction')
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia')
        self.payload['id'] = self.reaction.id
        super(DeletePerformedReaction, self).setUp()

    def tests_deleted(self):
        self.assertFalse(PerformedReaction.objects.filter(reference='turkish_delight', labGroup__title='narnia').exists())


@logsInAs('Aslan', 'old_magic')
@createsUser('WhiteQueen', 'New Magic')
@signsExampleLicense('Aslan')
@signsExampleLicense('WhiteQueen')
@joinsLabGroup('Aslan', 'narnia')
@joinsLabGroup('WhiteQueen', 'WhiteQueensArmy')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsPerformedReaction('WhiteQueensArmy', 'WhiteQueen', 'turkish_delight')
@usesCsrf
class DeleteSomeoneElsesReaction(PostHttpSessionTest, redirectionMixinFactory(1)):
    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes
    url = PostHttpSessionTest.url + reverse('deleteReaction')

    def setUp(self):
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='WhiteQueensArmy')
        self.payload['id'] = self.reaction.id
        super(DeleteSomeoneElsesReaction, self).setUp()

    def tests_deleted(self):
        self.assertTrue(PerformedReaction.objects.filter(reference='turkish_delight', labGroup__title='narnia').exists())


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@usesCsrf
class DeleteNonexistentReaction(PostHttpSessionTest, redirectionMixinFactory(1)):

    url = PostHttpSessionTest.url + reverse('deleteReaction')
    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes

    def setUp(self):
        self.payload['id'] = 5
        super(DeleteNonexistentReaction, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@usesCsrf
class InvalidatePerformedReaction(PostHttpSessionTest, redirectionMixinFactory(1)):

    url = PostHttpSessionTest.url + reverse('invalidateReaction')
    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes

    def setUp(self):
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia')
        self.payload['id'] = self.reaction.id
        super(InvalidatePerformedReaction, self).setUp()

    def tests_deleted(self):
        self.assertFalse(PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').valid)


@logsInAs('Aslan', 'old_magic')
@createsUser('WhiteQueen', 'New Magic')
@signsExampleLicense('Aslan')
@signsExampleLicense('WhiteQueen')
@joinsLabGroup('Aslan', 'narnia')
@joinsLabGroup('WhiteQueen', 'WhiteQueensArmy')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsPerformedReaction('WhiteQueensArmy', 'WhiteQueen', 'turkish_delight')
@usesCsrf
class InvalidateSomeoneElsesReaction(PostHttpSessionTest, redirectionMixinFactory(1)):
    url = PostHttpSessionTest.url + reverse('invalidateReaction')
    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes

    def setUp(self):
        self.reaction = PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='WhiteQueensArmy')
        self.payload['id'] = self.reaction.id
        super(InvalidateSomeoneElsesReaction, self).setUp()

    def tests_deleted(self):
        self.assertTrue(PerformedReaction.objects.get(reference='turkish_delight', labGroup__title='narnia').valid)


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@usesCsrf
class InvalidateNonexistentReaction(PostHttpSessionTest, redirectionMixinFactory(1)):

    url = PostHttpSessionTest.url + reverse('invalidateReaction')
    testCodes = ['ba960469-5fad-4142-a0a1-a10b37e9432e'] + reactionBaseCodes

    def setUp(self):
        self.payload['id'] = 5
        super(InvalidateNonexistentReaction, self).setUp()


@logsInAs('Aslan', 'old_magic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsCompoundRole('Org', 'Organic')
@createsCompoundRole('inOrg', 'inOrganic')
@usesCsrf
class PostReactantAddCreatingValid(PostHttpSessionTest, redirectionMixinFactory(5)):  # we expect 5 redirections because we have initialised no manual reaction descriptors
    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93'] + reactionBaseCodes
    _params = {'creating': True}
    _payload = {
        'quantities-TOTAL_FORMS': '1',
        'quantities-INITIAL_FORMS': '0',
        'quantities-MIN_NUM_FORMS': '0',
        'quantities-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        self.url = self.url + reverse('addCompoundDetails', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight').id})
        self.payload['quantities-0-id'] = ''
        self.payload['quantities-0-role'] = CompoundRole.objects.get(label='Org').id
        self.payload['quantities-0-compound'] = Compound.objects.get(abbrev='2-amep').id
        self.payload['quantities-0-amount'] = '22'
        super(PostReactantAddCreatingValid, self).setUp()

    def tearDown(self):
        CompoundQuantity.objects.all().delete()
        super(PostReactantAddCreatingValid, self).tearDown()


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsCompoundRole('Org', 'Organic')
@createsCompoundRole('inOrg', 'inOrganic')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
@usesCsrf
class PostReactantAddCreatingValid2(PostHttpSessionTest, redirectionMixinFactory(2)):  # we expect 4 redirections because we have initialised no manual reaction descriptors
    testCodes = ['9fa2cfb6-aabe-40f7-80ea-4ecbcf8c0bda', '634d88bb-9289-448b-a3dc-548ff4c6cda1'] + reactionBaseCodes
    _params = {'creating': True}
    _payload = {
        'quantities-TOTAL_FORMS': '1',
        'quantities-INITIAL_FORMS': '0',
        'quantities-MIN_NUM_FORMS': '0',
        'quantities-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        self.url = self.url + reverse('addCompoundDetails', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight').id})
        self.payload['quantities-0-id'] = ''
        self.payload['quantities-0-role'] = CompoundRole.objects.get(label='Org').id
        self.payload['quantities-0-compound'] = Compound.objects.get(abbrev='2-amep').id
        self.payload['quantities-0-amount'] = '22'
        super(PostReactantAddCreatingValid2, self).setUp()

    def tearDown(self):
        CompoundQuantity.objects.all().delete()
        super(PostReactantAddCreatingValid2, self).tearDown()


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsCompoundRole('Org', 'Organic')
@createsCompoundRole('inOrg', 'inOrganic')
@usesCsrf
class PostReactantAddCreatingInvalid(PostHttpSessionTest):
    _params = {'creating': True}
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _payload = {
        'quantities-TOTAL_FORMS': '1',
        'quantities-INITIAL_FORMS': '0',
        'quantities-MIN_NUM_FORMS': '0',
        'quantities-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        self.url = self.url + reverse('addCompoundDetails', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight').id})
        self.payload['quantities-0-id'] = ''
        self.payload['quantities-0-role'] = CompoundRole.objects.get(label='Org').id
        self.payload['quantities-0-compound'] = Compound.objects.get(abbrev='2-amep').id
        self.payload['quantities-0-amount'] = '-1'
        super(PostReactantAddCreatingInvalid, self).setUp()


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsCompoundRole('Org', 'Organic')
@createsCompoundRole('inOrg', 'inOrganic')
@createsCompoundQuantity('turkish_delight', '2-amep', 'Org', '2.12')
@usesCsrf
class PostReactantEditingValid(PostHttpSessionTest, redirectionMixinFactory(1)):  # this is the same view so the invalid case is covered
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _payload = {
        'quantities-TOTAL_FORMS': '1',
        'quantities-INITIAL_FORMS': '1',
        'quantities-MIN_NUM_FORMS': '0',
        'quantities-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        rxn = PerformedReaction.objects.get(reference='turkish_delight')
        self.url = self.url + reverse('addCompoundDetails', kwargs={'rxn_id': rxn.id})
        self.quantity = CompoundQuantity.objects.get(reaction=rxn, reaction__labGroup__title='narnia', compound__abbrev='2-amep')
        self.payload['quantities-0-id'] = self.quantity.id
        self.payload['quantities-0-role'] = CompoundRole.objects.get(label='Org').id
        self.payload['quantities-0-compound'] = Compound.objects.get(abbrev='2-amep').id
        self.payload['quantities-0-amount'] = '15'
        super(PostReactantEditingValid, self).setUp()
        self.quantity.refresh_from_db()

    def test_edit(self):
        self.assertEqual(self.quantity.amount, 15)


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsCompoundRole('Org', 'Organic')
@createsCompoundRole('inOrg', 'inOrganic')
@createsCompoundQuantity('turkish_delight', '2-amep', 'Org', '2.12')
@usesCsrf
class PostReactantDeleteValid(PostHttpSessionTest, redirectionMixinFactory(1)):  # we expect 4 redirections because we have initialised no manual reaction descriptors
    testCodes = ['7b3b6668-981a-4a11-8dc4-23107187de93'] + reactionBaseCodes
    _payload = {
        'quantities-TOTAL_FORMS': '1',
        'quantities-INITIAL_FORMS': '1',
        'quantities-MIN_NUM_FORMS': '0',
        'quantities-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        rxn = PerformedReaction.objects.get(reference='turkish_delight')
        self.url = self.url + reverse('addCompoundDetails', kwargs={'rxn_id': rxn.id})
        cq = CompoundQuantity.objects.get(compound__abbrev='2-amep', reaction=rxn)
        self.payload['quantities-0-role'] = cq.role.id
        self.payload['quantities-0-compound'] = cq.compound.id
        self.payload['quantities-0-amount'] = cq.amount
        self.payload['quantities-0-DELETE'] = 'on'
        self.payload['quantities-0-id'] = CompoundQuantity.objects.get(compound__abbrev='2-amep', reaction=rxn).id
        super(PostReactantDeleteValid, self).setUp()

    def test_delete(self):
        rxn = PerformedReaction.objects.get(reference='turkish_delight')
        self.assertEqual(CompoundQuantity.objects.filter(compound__abbrev='2-amep', reaction=rxn).count(), 0)


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
@usesCsrf
class CreateReactionDescValCreating(PostHttpSessionTest, redirectionMixinFactory(3)):
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _params = {'creating': True}
    _payload = {
        'createOrdDescVals-TOTAL_FORMS': '1',
        'createOrdDescVals-INITIAL_FORMS': '0',
        'createOrdDescVals-MIN_NUM_FORMS': '0',
        'createOrdDescVals-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        self.url = self.url + reverse('createOrdDescVals', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight').id})
        self.payload['createOrdDescVals-0-id'] = ''
        self.payload['createOrdDescVals-0-descriptor'] = OrdRxnDescriptor.objects.get(heading='deliciousness').id
        self.payload['createOrdDescVals-0-value'] = '0'
        super(CreateReactionDescValCreating, self).setUp()

    def test_created(self):
        self.assertTrue(OrdRxnDescriptorValue.objects.all().exists())


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
@usesCsrf
class CreateReactionDescValEditing(PostHttpSessionTest, redirectionMixinFactory(1)):  # no edit test required- it uses the same functionality
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _payload = {
        'createOrdDescVals-TOTAL_FORMS': '1',
        'createOrdDescVals-INITIAL_FORMS': '0',
        'createOrdDescVals-MIN_NUM_FORMS': '0',
        'createOrdDescVals-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        self.url = self.url + reverse('createOrdDescVals', kwargs={'rxn_id': PerformedReaction.objects.get(reference='turkish_delight').id})
        self.payload['createOrdDescVals-0-id'] = ''
        self.payload['createOrdDescVals-0-descriptor'] = OrdRxnDescriptor.objects.get(heading='deliciousness').id
        self.payload['createOrdDescVals-0-value'] = '0'
        super(CreateReactionDescValEditing, self).setUp()

    def test_created(self):
        self.assertTrue(OrdRxnDescriptorValue.objects.all().exists())


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
@createsOrdRxnDescriptorValue('narnia', 'turkish_delight', 'deliciousness', 3)
@usesCsrf
class DeleteReactionDescVal(PostHttpSessionTest, redirectionMixinFactory(1)):
    testCodes = ['008d2580-5be2-4112-8297-a9e53490bb6d', 'dc1d5961-a9e7-44d8-8441-5b8402a01c06'] + reactionBaseCodes
    _payload = {
        'createOrdDescVals-TOTAL_FORMS': '1',
        'createOrdDescVals-INITIAL_FORMS': '1',
        'createOrdDescVals-MIN_NUM_FORMS': '0',
        'createOrdDescVals-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        rxn = PerformedReaction.objects.get(reference='turkish_delight')
        self.url = self.url + reverse('createOrdDescVals', kwargs={'rxn_id': rxn.id})
        self.payload['createOrdDescVals-0-descriptor'] = OrdRxnDescriptor.objects.get(heading='deliciousness')
        self.payload['createOrdDescVals-0-value'] = '0'
        self.payload['createOrdDescVals-0-DELETE'] = 'on'
        self.payload['createOrdDescVals-0-id'] = OrdRxnDescriptorValue.objects.get(reaction=rxn, descriptor__heading='deliciousness').id
        super(DeleteReactionDescVal, self).setUp()

    def test_deleted(self):
        self.assertFalse(OrdRxnDescriptorValue.objects.all().exists())


@logsInAs('Aslan', 'oldmagic')
@signsExampleLicense('Aslan')
@joinsLabGroup('Aslan', 'narnia')
@loadsCompoundsFromCsv('narnia', 'compound_spread_test1.csv')
@createsPerformedReaction('narnia', 'Aslan', 'turkish_delight')
@createsOrdRxnDescriptor('deliciousness', 0, 4)
@createsOrdRxnDescriptorValue('narnia', 'turkish_delight', 'deliciousness', 3)
@usesCsrf
class EditReactionDescValInvalid(PostHttpSessionTest):
    testCodes = ['9fa2cfb6-aabe-40f7-80ea-4ecbcf8c0bda', '634d88bb-9289-448b-a3dc-548ff4c6cda1'] + reactionBaseCodes
    _payload = {
        'createOrdDescVals-TOTAL_FORMS': '1',
        'createOrdDescVals-INITIAL_FORMS': '1',
        'createOrdDescVals-MIN_NUM_FORMS': '0',
        'createOrdDescVals-MAX_NUM_FORMS': '1000'
    }

    def setUp(self):
        rxn = PerformedReaction.objects.get(reference='turkish_delight')
        self.url = self.url + reverse('createOrdDescVals', kwargs={'rxn_id': rxn.id})
        self.payload['createOrdDescVals-0-descriptor'] = OrdRxnDescriptor.objects.get(heading='deliciousness').id
        self.payload['createOrdDescVals-0-value'] = '-1'
        self.payload['createOrdDescVals-0-id'] = OrdRxnDescriptorValue.objects.get(reaction=rxn, descriptor__heading='deliciousness').id
        super(EditReactionDescValInvalid, self).setUp()

    def test_created(self):
        self.assertTrue(OrdRxnDescriptorValue.objects.all().exists())

suite = unittest.TestSuite([
    loadTests(GetReactionCreate),
    loadTests(PostReactionCreateValid),
    loadTests(PostReactionCreateInvalid),
    loadTests(GetReactionEdit),
    loadTests(GetReactionEdit2),
    loadTests(GetSomeoneElsesReactionEdit),
    loadTests(GetNonexistentReactionEdit),
    loadTests(PostReactionEditValid),
    loadTests(PostReactionEditInvalid),
    loadTests(DeletePerformedReaction),
    loadTests(DeleteSomeoneElsesReaction),
    loadTests(DeleteNonexistentReaction),
    loadTests(InvalidatePerformedReaction),
    loadTests(InvalidateSomeoneElsesReaction),
    loadTests(InvalidateNonexistentReaction),
    loadTests(PostReactantAddCreatingValid),
    loadTests(PostReactantAddCreatingValid2),
    loadTests(PostReactantAddCreatingInvalid),
    loadTests(PostReactantEditingValid),
    loadTests(PostReactantDeleteValid),
    loadTests(CreateReactionDescValCreating),
    loadTests(CreateReactionDescValEditing),
    loadTests(DeleteReactionDescVal),
    loadTests(EditReactionDescValInvalid)
])

if __name__ == '__main__':
    runTests(suite)