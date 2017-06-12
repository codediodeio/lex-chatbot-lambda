import unittest
import bot

test_input = {
      "currentIntent": {
        "slots": {
          "buyer": "Joe",
          "seller": "John",
          "buyerAddress": None,
        },
        "name": "BillOfSale",
        "confirmationStatus": "None"
      },
      "bot": {
        "alias": "$LATEST",
        "version": "$LATEST",
        "name": "TestBot"
      },
      "userId": "uid",
    #   "invocationSource": "ElicitSlotCodeHook",
      "invocationSource": "FulfillmentCodeHook",
      "outputDialogMode": "Text",
      "messageVersion": "1.0",
      "inputTranscript": "user message",
      "sessionAttributes": {
      }
  }

class LambdaTestCase(unittest.TestCase):

    def test_not_none(self):
        """Response is not None"""
        res = bot.lambda_handler(test_input)
        self.assertIsNotNone(res)

    def test_fulfillment(self):
        """Response is fulfilled"""
        res = bot.lambda_handler(test_input)
        self.assertEqual(res['dialogAction']['fulfillmentState'], 'Fulfilled')


if __name__ == '__main__':
    unittest.main()
