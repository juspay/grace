{
  "request_ref_id": {
    "id": "{{REFERENCE_ID}}"
  },
  "amount": {{AMOUNT}},
  "minor_amount": {{AMOUNT}},
  "currency": "{{CURRENCY}}",
  "capture_method": "{{CAPTURE_METHOD}}",
  "auth_type": "NO_THREE_DS",
  "payment_method": {
    "card": {
      "card_number": {
        "value": "{{CARD_NUMBER}}"
      },
      "card_cvc": {
        "value": "{{CARD_CVC}}"
      },
      "card_exp_month": {
        "value": "{{CARD_EXP_MONTH}}"
      },
      "card_exp_year": {
        "value": "{{CARD_EXP_YEAR}}"
      },
      "card_network": "{{CARD_NETWORK}}"
    }
  },
  "address": {
    "billing_address": {
      "first_name": {
        "value": "{{FIRST_NAME}}"
      },
      "last_name": {
        "value": "{{LAST_NAME}}"
      },
      "line1": {
        "value": "{{ADDRESS_LINE1}}"
      },
      "city": {
        "value": "{{CITY}}"
      },
      "state": {
        "value": "{{STATE}}"
      },
      "zip_code": {
        "value": "{{ZIP_CODE}}"
      },
      "country_alpha2_code": "{{COUNTRY}}",
      "email": {
        "value": "{{EMAIL}}"
      },
      "phone_number": {
        "value": "{{PHONE_NUMBER}}"
      },
      "phone_country_code": "{{PHONE_COUNTRY_CODE}}"
    }
  },
  "return_url": "{{RETURN_URL}}",
  "webhook_url": "{{WEBHOOK_URL}}",
  "order_category": "pay",
  "enrolled_for_3ds": false,
  "request_incremental_authorization": false,
  "metadata": {
    "order_id": "order_{{CONNECTOR_NAME}}_{{TIMESTAMP}}",
    "customer_email": "{{EMAIL}}",
    "description": "Test payment for {{CONNECTOR_NAME}}"
  }
}
