import math
import datetime
import time
import os
import logging
import json
import re
import urllib2

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LexEvent:
    """handles incoming and outgoing params to Lex ann validates slots"""

    def __init__(self, event):
        self.event = event
        self.slots = event['currentIntent']['slots']
        self.intent = event['currentIntent']['name']
        self.input_text = event['inputTranscript']
        self.sess_attr = event['sessionAttributes']
        self.invocation = event['invocationSource']


    ### Helpers to control state of the conversation

    def delegate(self, intent=None):
        return {
            'sessionAttributes': self.sess_attr,
            'dialogAction': {
                'type': 'Delegate',
                'slots': self.slots
            }
        }

    def fulfill(self, msg="Your document is complete."):
        return {
            'sessionAttributes': self.sess_attr,
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Fulfilled',
                "message": {
                  "contentType": "PlainText",
                  "content": msg
                }
            }
        }



    def elicit_slot(self, err):
        return {
            'sessionAttributes': self.sess_attr,
            'dialogAction': {
                'type': 'ElicitSlot',
                'intentName': self.intent,
                'slots': self.slots,
                'slotToElicit': err['violatedSlot'],
                'message': {'contentType': 'PlainText', 'content': err['message'] }
            }
        }

    def elicit_intent(self, msg="How can I help you?"):
        return {
             "sessionAttributes": self.sess_attr,
             "dialogAction": {
                "type": "ElicitIntent",
                "message": {
                  "contentType": "PlainText",
                  "content": msg
            }
        }
    }

    #### Slot Validators

    def val_error(self, slot, msg):
        res = {"isValid": False, "violatedSlot": slot, 'message': msg }
        return res

    def validates_presence(self, slot, msg=None):
        if not self.slots[slot]: # raise val_error
            if not msg:
                msg = "What is the {}?".format(slot)
            err = self.val_error(slot, msg)
            return self.elicit_slot(err)

    def validates_in(self, iterable, slot, msg=None):
        if self.slots[slot] not in iterable:
            if not msg:
                iter_list = ", ".join([str(x) for x in iterable])
                msg = "Your {0} must be one of the following: {1}".format(slot, iter_list)
            err = self.val_error(slot, msg)
            return self.elicit_slot(err)

    def validates_length(self, rng, slot, msg=None):
        if not self.slots[slot]: return
        # rng = (min, max)
        if len(self.slots[slot]) > rng[1]:
            if not msg:
                msg = "Your {0} is too large. I can handle {1} characters max.".format(slot, rng[1])
            err = self.val_error(slot, msg)
            return self.elicit_slot(err)

        if len(self.slots[slot]) < rng[0]:
            if not msg:
                msg = "Your {0} is too small. I need at least {1} characters.".format(slot, rng[0])
            err = self.val_error(slot, msg)
            return self.elicit_slot(err)


    def validates_pattern(self, regex, slot, msg=None):
        if not self.slots[slot]: return

        pattern = re.compile(regex)
        if not pattern.match(self.slots[slot]):
            if not msg:
                msg = "Your {0} seems to have an invalid format".format(slot)
            err = self.val_error(slot, msg)
            return self.elicit_slot(err)


    def run_validation(self, validators):
        for error in validators:
            if error:
                return error

        return lex.delegate()


def deliver_document(lex):
    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill("Your document has been emailed!")

    validators = [
        lex.validates_presence('emailAddress', "What email address would you like this document sent to?"),
        lex.validates_pattern("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                    "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                    "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)",
        'emailAddress', ""),
    ]

    return lex.run_validation(validators)


def bill_of_sale(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('buyer', "What is the buyer's name? "),
        lex.validates_presence('buyerAddress', "What is the buyer's address?"),
        lex.validates_presence('seller', "What is the seller's name?"),
        lex.validates_presence('sellerAddress', "What is the seller's address?"),
        lex.validates_presence('itemSold', "What is the item being sold called? Brand, make, model or name"),
        lex.validates_presence('serial', "What is the serial number? If any"),
        lex.validates_presence('description', "Briefly describe the item or any special characteristics"),
        lex.validates_presence('price', "What is the total final selling price in dollars?, i.e 500 "),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def boat_bill_of_sale(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('buyer', "What is the name of the person buying the vessel? "),
        lex.validates_presence('buyerAddress', "What is the buyer's address?"),
        lex.validates_presence('seller', "What is the seller's name?"),
        lex.validates_presence('sellerAddress', "What is the seller's address?"),
        lex.validates_presence('itemMake', "What is the boat's make?"),
        lex.validates_presence('itemModel', "What is the boat's model?"),
        lex.validates_presence('year', "What is the boat's year of construction?"),
        lex.validates_presence('serial', "What is the Hull Identification Number (HIN)"),
        lex.validates_presence('price', "What is the total final selling price in dollars?"),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def vehicle_bill_of_sale(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('buyer', "What is the name of the person buying the vehicle? "),
        lex.validates_presence('buyerAddress', "What is the buyer's address?"),
        lex.validates_presence('seller', "What is the seller's name?"),
        lex.validates_presence('sellerAddress', "What is the seller's address?"),
        lex.validates_presence('itemMake', "What is the vehicle's make?"),
        lex.validates_presence('itemModel', "What is the vehicle's model?"),
        lex.validates_presence('year', "What year is the vehicle?"),
        lex.validates_presence('itemType', "What type of vehicle is this? Car, Truck, ATV, Hovercraft, etc...?"),
        lex.validates_presence('odometer', "What is the current odometer reading?"),
        lex.validates_presence('serial', "What is the Vehicle Identification Number (VIN)"),
        lex.validates_presence('price', "What is the total final selling price in dollars? "),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def animal_bill_of_sale(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill("Your animal bill of sale is complete!")

    validators = [
        lex.validates_presence('buyer', "What is the name of the person buying the animal? "),
        lex.validates_presence('buyerAddress', "What is the buyer's address?"),
        lex.validates_presence('seller', "What is the seller's name?"),
        lex.validates_presence('sellerAddress', "What is the seller's address?"),
        lex.validates_presence('itemType', "What type of animal is being sold? Dog, Cat, Snake, Turtle, etc."),
        lex.validates_presence('itemMake', "What is the animal's breed?"),
        lex.validates_presence('year', "What year was the animal born?"),
        lex.validates_presence('color', "What color is the animal?"),
        lex.validates_presence('serial', "What is the animal's ID or chip number, if any?"),
        lex.validates_presence('description', "Briefly describe any other important details"),
        lex.validates_presence('price', "What is the total final selling price in dollars?"),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def firearm_bill_of_sale(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('buyer', "What is the name of the person buying the firearm? "),
        lex.validates_presence('buyerAddress', "What is the buyer's address?"),
        lex.validates_presence('seller', "What is the seller's name?"),
        lex.validates_presence('sellerAddress', "What is the seller's address?"),
        lex.validates_presence('itemMake', "What is the firearm make or manufacturer?"),
        lex.validates_presence('itemModel', "What is the firearm model?"),
        lex.validates_presence('itemType', "What is the firearm caliber?"),
        lex.validates_presence('serial', "What is the firearm's serial number?"),
        lex.validates_presence('price', "What is the total final selling price in dollars?"),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def general_contract(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('provider', "What is the name of the Promisor or Provider in the contract?"),
        lex.validates_presence('providerAddress', "What is the Promisor's address?"),
        lex.validates_presence('receiver', "What is the Promisee's name?"),
        lex.validates_presence('receiverAddress', "What is the Promisee's address?"),
        lex.validates_presence('description', "What are the terms of your contract? Describe the legal relationship between the promisor and promisee."),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place.")
    ]

    return lex.run_validation(validators)

def pool_service_contract(lex):

    if lex.invocation == "FulfillmentCodeHook":
        # if sess email, send via email, else get an email
        return lex.fulfill()

    validators = [
        lex.validates_presence('provider', "What is the name of the person or company providing pool services?"),
        lex.validates_presence('providerAddress', "What is the provider's address?"),
        lex.validates_presence('receiver', "What is the client's name?"),
        lex.validates_presence('receiverAddress', "What is the client's address?"),
        lex.validates_presence('interval', "How often will the client be billed? Monthly, Yearly, etc."),
        lex.validates_presence('rate', "How much will be charged per billing cycle in dollars?"),
        lex.validates_presence('frequency', "How often will pool services be conducted? Weekly, Monthly, etc."),
        lex.validates_presence('description', "What type of services will be offered? Chemical balancing, filter backwashing, debris skimming, etc."),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)


def promissory_note(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('provider', "What is the name of the person or company lending money?"),
        lex.validates_presence('providerAddress', "What lender's address?"),
        lex.validates_presence('receiver', "What is the borrower's name?"),
        lex.validates_presence('receiverAddress', "What is the borrower's address?"),
        lex.validates_presence('principal', "What is the principal balance of the loan?"),
        lex.validates_presence('interest', "What is the interest rate as a percent? "),
        lex.validates_presence('payment', "What is the payment amount per period?"),
        lex.validates_presence('periods', "How many months will the loan last?"),
        lex.validates_presence('startDate', "What date will interest start accruing?"),
        lex.validates_presence('itemSold', "What is the borrower's consideration? In other words, what is this loan for? i.e $5000 cash, Motorcycle, Consulting Services, etc."),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)

def due_on_demand_note(lex):

    if lex.invocation == "FulfillmentCodeHook":
        return lex.fulfill()

    validators = [
        lex.validates_presence('provider', "What is the name of the person or company lending money?"),
        lex.validates_presence('providerAddress', "What lender's address?"),
        lex.validates_presence('receiver', "What is the borrower's name?"),
        lex.validates_presence('receiverAddress', "What is the borrower's address?"),
        lex.validates_presence('principal', "What is the principal balance of the loan?"),
        lex.validates_presence('interest', "What is the interest rate?"),
        lex.validates_presence('itemSold', "What is this loan for? i.e $5000 cash, Motorcycle, Consulting Services, etc."),
        lex.validates_presence('jurisdiction', "Where should this contract be enforced? Usually it's where the transaction takes place."),
    ]

    return lex.run_validation(validators)



def help_user(lex):
    return lex.fulfill("Start by telling me what type of legal document you need? Such as 'bill of sale', 'promissory note', 'pool service contract', etc. Or you can say 'show all'")

def show_documents(lex):
    return lex.fulfill("Here's the full list of documents I can draft. Which one would you like to get started?")

def not_understood(lex):
    return lex.fulfill("I did not understand that... Can you rephrase your message?")

def developer_info(lex):
    return lex.fulfill("I owe my inception to JeffDelaney.me. Contact him with your questions.")



def dispatch(lex):
    if lex.intent == "BasicHelp":
        return help_user(lex)
    if lex.intent == "ShowDocuments":
        return show_documents(lex)
    if lex.intent == "DeveloperInfo":
        return developer_info(lex)
    if lex.intent == "DeliverDocument":
        return deliver_document(lex)
    if lex.intent == "BillOfSale":
        return bill_of_sale(lex)
    if lex.intent == "BoatBillOfSale":
        return boat_bill_of_sale(lex)
    if lex.intent == "VehicleBillOfSale":
        return vehicle_bill_of_sale(lex)
    if lex.intent == "AnimalBillOfSale":
        return animal_bill_of_sale(lex)
    if lex.intent == "FirearmBillOfSale":
        return firearm_bill_of_sale(lex)
    if lex.intent == "DueOnDemandNote":
        return due_on_demand_note(lex)
    if lex.intent == "PromissoryNote":
        return promissory_note(lex)
    if lex.intent == "GeneralContract":
        return general_contract(lex)
    if lex.intent == "PoolServiceContract":
        return pool_service_contract(lex)
    else:
        return not_understood(lex)


def lambda_handler(event, context=None):
    lex = LexEvent(event)
    logger.info(('IN', event))

    try:
        res = dispatch(lex)
        logger.info(('OUT', res))
        return res
    except Exception as e:
        logger.error(e)
