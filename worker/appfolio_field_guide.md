# AppFolio Tenant Receipts Form Field Guide

## 🎯 Target URL
`https://<your-domain>.appfolio.com/accounting/tenant_receipts/new`

## 🔐 Authentication Configuration

### Login Details:
```yaml
login:
  url: "https://<your-domain>.appfolio.com/users/sign_in"
  username_selector: 'input[name="user[email]"]'
  password_selector: 'input[name="user[password]"]'
  submit_selector: 'button[type="submit"]'
```

## 📋 Required Excel Columns

Your Excel/CSV file should have these columns:

```csv
TenantName,Amount,ReceiptDate,Remarks,Reference,CashAccount,PaymentType
John Smith,1200.00,01/15/2024,Monthly rent,REF001,Operating Account,Check
Jane Doe,1350.00,01/15/2024,Rent payment,REF002,Operating Account,Online
```

## 🔧 Form Field Mapping

### Receipt Header Section:
```yaml
field_mapping:
  # Tenant (searchable combobox)
  TenantName: '#new_form .js-payer input[type="search"], #new_form .js-payer input[type="text"]'
  
  # Amount field
  Amount: '#receivable_payment_amount'
  
  # Receipt Date (MM/DD/YYYY format)
  ReceiptDate: '#receivable_payment_occurred_on, input[name="receivable_payment[occurred_on]"]'
  
  # Remarks/Notes
  Remarks: '#receivable_payment_remarks, input[name="receivable_payment[remarks]"], textarea[name="receivable_payment[remarks]"]'
  
  # Reference number
  Reference: '#receivable_payment_reference, input[name="receivable_payment[reference]"]'
  
  # Cash Account (dropdown)
  CashAccount: '#receivable_payment_cash_account_id, select[name="receivable_payment[cash_account_id]"]'
  
  # Payment Type (dropdown or async select)
  PaymentType: '#receivable_payment_payment_type_id, select[name="receivable_payment[payment_type_id]"], [aria-label="Payment Type"] input'
```

## 🚀 Complete Configuration

```yaml
appfolio_tenant_receipts:
  entrypoint: "https://<your-domain>.appfolio.com/accounting/tenant_receipts/new"
  
  login:
    url: "https://<your-domain>.appfolio.com/users/sign_in"
    username_selector: 'input[name="user[email]"]'
    password_selector: 'input[name="user[password]"]'
    submit_selector: 'button[type="submit"]'

  steps:
    - name: "Receipt Header"
      wait_selector: '#new_form'
      bindings:
        - column: "TenantName"
          selector: '#new_form .js-payer input[type="search"], #new_form .js-payer input[type="text"]'
          input_type: "text"
          required: true

        - column: "Amount"
          selector: '#receivable_payment_amount'
          input_type: "text"
          required: true

        - column: "ReceiptDate"
          selector: '#receivable_payment_occurred_on, input[name="receivable_payment[occurred_on]"]'
          input_type: "date"
          format: "%m/%d/%Y"
          required: true

        - column: "Remarks"
          selector: '#receivable_payment_remarks, input[name="receivable_payment[remarks]"], textarea[name="receivable_payment[remarks]"]'
          input_type: "text"

        - column: "Reference"
          selector: '#receivable_payment_reference, input[name="receivable_payment[reference]"]'
          input_type: "text"

        - column: "CashAccount"
          selector: '#receivable_payment_cash_account_id, select[name="receivable_payment[cash_account_id]"]'
          input_type: "select"

        - column: "PaymentType"
          selector: '#receivable_payment_payment_type_id, select[name="receivable_payment[payment_type_id]"], [aria-label="Payment Type"] input'
          input_type: "text"

    - name: "Distribute Lines"
      wait_selector: 'table'
      bindings: []

  submit:
    submit_selector: 'button[type="submit"], button:has-text("Post"), button:has-text("Save")'
    confirm_selector: 'text=/Receipt|saved|posted/i'
    confirm_text: null

  anti_bot:
    human_delay_min_ms: 650
    human_delay_max_ms: 1400
    retry_attempts: 3
    screenshot_on_error: true
```

## 🧪 Testing Commands

### Chat Command:
```
"Start filling forms at https://sairealty.appfolio.com/accounting/tenant_receipts/new"
```

### API Command:
```bash
curl -X POST http://localhost:8000/jobs/{job_id}/fill-forms \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "your-job-id",
    "website_url": "https://sairealty.appfolio.com/accounting/tenant_receipts/new",
    "field_mapping": {
      "TenantName": "#new_form .js-payer input[type=\"search\"]",
      "Amount": "#receivable_payment_amount",
      "ReceiptDate": "#receivable_payment_occurred_on"
    },
    "submit_selector": "button[type=\"submit\"]"
  }'
```

## 📝 Key Features

### Special Handling:
- **Tenant Search**: Uses searchable combobox (`.js-payer`)
- **Date Format**: Expects MM/DD/YYYY format
- **Amount**: Accepts decimal values (1200.00)
- **Multiple Selectors**: Fallback selectors for reliability
- **Anti-Bot**: Human-like delays (650-1400ms)
- **Screenshots**: Captures errors automatically

### Required Fields:
- ✅ **TenantName** - Must match existing tenant
- ✅ **Amount** - Payment amount  
- ✅ **ReceiptDate** - Date in MM/DD/YYYY format

### Optional Fields:
- Remarks/Notes
- Reference number
- Cash Account selection
- Payment Type selection

## ⚠️ Important Notes

1. **Authentication Required**: Must login before accessing forms
2. **Tenant Validation**: Tenant names must exist in AppFolio system
3. **Date Format**: Use MM/DD/YYYY format for dates
4. **Amount Format**: Use decimal format (1200.00)
5. **Anti-Detection**: Built-in delays prevent bot detection