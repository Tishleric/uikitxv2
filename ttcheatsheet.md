Here's the minimum that must be in every call, plus a working token-request example you can drop straight into Postman, curl, or Python.  (All paths below assume the **UAT** environment; switch `ext_uat_cert` → `ext_prod_live` for live.)

---

### 1 Get a token from **ttid**

```
POST https://apigateway.trade.tt/ttid/ext_uat_cert/token?requestId=<app>-<company>--<guid>
Content-Type: application/x-www-form-urlencoded
x-api-key: <YOUR_API_KEY>

grant_type=user_app&app_key=<YOUR_API_KEY>:<YOUR_API_SECRET>
```

* **Body** is **URL-encoded form data** – **not** JSON.
  Required keys are exactly `grant_type=user_app` and `app_key=<key>:<secret>` (the same string you copied from Setup). ([GitHub][1])

* **requestId** must be a query-string param, lower-camel-case, and follow
  `<app_name>-<company_name>--<GUID>`
  Avoid spaces and these characters: \`\$ & + , / : ; = ? @ " < > # % { } | \ ^ \~ \[ ] \`\`.  ([Trading Technologies Library][2])

A successful call returns JSON like:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR...",
  "token_type": "bearer",
  "seconds_until_expiry": 3600
}
```

---

### 2 Make authorised requests

Add **two** headers to every subsequent call:

```
x-api-key: <YOUR_API_KEY>
Authorization: Bearer <access_token>
```

* Note the normal HTTP **colon** (`:`) after `Authorization` and the single blank **space** before the token.
  The doc page shows `Authorization=Bearer <token>` only because it lists headers in **key=value** style; in HTTP you still send them as `Header-Name: value`. ([Trading Technologies Library][2])
* For `GET` requests, also include `accept: application/json` (lowercase confirmed).
* **Crucially, for `GET` requests, OMIT the `Content-Type` header.** Sending `Content-Type` on a GET request can confuse the AWS API Gateway (which TT uses) and lead to it misinterpreting the `Authorization` header, causing a 403 error with "Invalid key=value pair".

---

### 3 Quick examples

**curl**

```bash
guid=$(python - <<<'import uuid,sys;print(uuid.uuid4())')
token=$(curl -s -X POST \
  "https://apigateway.trade.tt/ttid/ext_uat_cert/token?requestId=myapp-myco--${guid}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "x-api-key: $TT_KEY" \
  --data-urlencode "grant_type=user_app" \
  --data-urlencode "app_key=$TT_SECRET" | jq -r '.access_token')

curl "https://apigateway.trade.tt/ttpds/ext_uat_cert/exchanges" \
  -H "x-api-key: $TT_KEY" \
  -H "Authorization: Bearer $token"
```

**Python (requests)** – distilled from the open-source client:

```python
import uuid, requests

API_KEY    = "00000000-0000-0000-0000-000000000000"
API_SECRET = "00000000-0000-0000-0000-000000000000:11111111-1111-1111-1111-111111111111"
ENV        = "ext_uat_cert"
APP        = "myapp"
COMPANY    = "myco"

base = "https://apigateway.trade.tt"
rid  = f"{APP}-{COMPANY}--{uuid.uuid4()}"

token_resp = requests.post(
    f"{base}/ttid/{ENV}/token",
    params={"requestId": rid},
    headers={"Content-Type": "application/x-www-form-urlencoded",
             "x-api-key": API_KEY},
    data={"grant_type": "user_app",
          "app_key": API_SECRET}
).json()

auth_hdrs = {
    "x-api-key": API_KEY,
    "Authorization": f"Bearer {token_resp['access_token']}",
    "accept": "application/json"
}

r = requests.get(f"{base}/ttpds/{ENV}/exchanges", params={"requestId": rid}, headers=auth_hdrs)
print(r.json())
```

---

### 4 Common pitfalls

| Pitfall                                                                  | Fix                                      |
| ------------------------------------------------------------------------ | ---------------------------------------- |
| Using `Authorization=Bearer ...` literally in the HTTP header              | Change to `Authorization: Bearer ...`      |
| Forgetting `x-api-key` on the **token** call                             | Required on every request                |
| Omitting the query-param `requestId`                                     | Generate a new GUID for each call        |
| Using spaces or special characters in `requestId`                        | Stick to letters, numbers, hyphens (`-`) |
| Sending JSON instead of `application/x-www-form-urlencoded` for `/token` | Use form data exactly as shown           |

---

### 5 Reference material & sample client

* **Official docs:** "Authentication and request IDs" – lists header names, token notes, and the requestId format. ([Trading Technologies Library][2])
* **Open-source Python client:** Shows a complete token workflow in `authenticator.py`. Handy if you need a tested reference implementation. ([GitHub][1])

Follow the pattern above and the TT gateway should accept your calls. If you still hit 401/403 errors, double-check that:

* your API key was created in the same **environment** you're calling, and
* the token hasn't expired (see `seconds_until_expiry` in the token response).

Let me know if anything's still blocking your integration!

[1]: https://github.com/isaaclm/tt-rest-api/raw/main/ttrest/authenticator.py "github.com"
[2]: https://library.tradingtechnologies.com/tt-rest/v2_uat/gs-token.html "TT Rest | Authentication and request IDs"


NEW SECTION

**Why that 403 happens**

"Invalid key=value pair (missing equal-sign) in Authorization header ..." is the generic error Amazon API Gateway emits when *the URL you hit does **not** match an endpoint that understands "Bearer <token>.".*
Because TT uses AWS Gateway under the hood, a request that lands on the **wrong domain or wrong path** is interpreted as a normal AWS-signed request; the gateway then tries to parse the `Authorization:` header as a SigV4 string (`Credential=...,SignedHeaders=...,Signature=...`) and complains that it can't find any `=` signs.

In your run-log the request went to

```
https://apigateway.trade.tt/ttpds/ext_uat_cert/exchanges
```

but the published base URL is

```
https://ttrestapi.trade.tt/ttpds/ext_uat_cert/exchanges
```

Notice the hostname (`ttrestapi.trade.tt`). Using the `apigateway.…` host will always give that 403, no matter how perfect your header is. The same rule holds for every TT REST service (`ttid`, `ttledger`, `ttmonitor`, ...)

---

### The canonical pattern

```text
# token call
POST https://ttrestapi.trade.tt/ttid/<env>/token?requestId=<app>-<co>--<GUID>
Content-Type: application/x-www-form-urlencoded
x-api-key: <API_KEY>

grant_type=user_app&app_key=<API_KEY>:<API_SECRET>

# all other calls
GET  https://ttrestapi.trade.tt/<service>/<env>/<endpoint>?requestId=<...>
x-api-key: <API_KEY>
Authorization: Bearer <access_token>
```

* `<env>` is `ext_uat_cert` or `ext_prod_live` (all lower-case).
* `requestId` **must** be lower-camel-case and contain no spaces or the listed special characters ([library.tradingtechnologies.com][1])
* The HTTP header is **`Authorization: Bearer <token>`** (colon + exactly one space). The equal-sign you see in the docs is just their way of showing "key=value"; don't put it in the real header.

---

### Minimal fix to your example script

```python
TT_API_BASE_URL = "https://ttrestapi.trade.tt"        #  <-- Correct base host

# In your API call function (e.g., simple_api_call.py main or api_example.py make_api_request):
headers = {
    "x-api-key": tt_config.TT_API_KEY,
    "accept": "application/json",  # Lowercase 'a' confirmed
    # NO 'Content-Type' for GET requests
}
auth_header = token_manager.get_auth_header()
headers.update(auth_header)

# ... rest of your request logic ...
```

Everything else in *simple_api_call.py* (headers, token manager, requestId generation) looks fine .

---

### Quick-check list when you still see 4xx

| Check                    | Typical slip                                                  |
| ------------------------ | ------------------------------------------------------------- |
| **Hostname**             | `apigateway.trade.tt` instead of `ttrestapi.trade.tt`         |
| **Case sensitivity**     | `TTPDS` / `TTID` instead of `ttpds` / `ttid`                  |
| **Authorization header** | `Authorization=Bearer...` (equal sign) or extra spaces/newlines |
| **x-api-key present**    | Forgetting to send it on *token* or data calls                |
| **requestId param**      | Missing, wrong case (`requestID`), or contains `&`, `%`, etc. |
| **Mixed environments**   | UAT token/key used against `ext_prod_live` or vice-versa      |

Correct the base URL first; in >90 % of cases the 403 disappears immediately. If anything's still unclear let me know and we'll step through the token handshake with `curl -v` to watch every byte on the wire.

[1]: https://library.tradingtechnologies.com/tt-rest/v2_uat/gs-token.html "TT Rest | Authentication and request IDs"

### Known `ttpds` (Product Data Service) Endpoints

Based on the TT REST API documentation UI, the following GET endpoints are available under `https://ttrestapi.trade.tt/ttpds/<env>/` (all require `requestId` query parameter and standard auth headers):

*   `/algodata`: Retrieves definitions for algo userparameters-related enumerated values.
*   `/algos`: Gets a list of algos.
*   `/algos/{algoId}/userparameters`: Gets algo user parameters.
*   `/currencyrates`: Retrieves the rate of exchange between currencies.
*   `/instrument/{instrumentId}`: Gets detailed information about an individual instrument given its ID.
*   `/instrumentdata`: Gets instrument reference data.
*   `/instruments`: Gets a list of instruments given a product type ID or a product ID.
*   `/markets`: Gets the list of markets. (Successfully tested)
*   `/miccodes`: Gets a list of Market Identification Codes (MIC).
*   `/mics`: Gets a list of Market Identification Codes (MIC).
*   `/product/{productId}`: Gets detailed information about a product given its ID.
*   `/productdata`: Gets product reference data.
*   `/productfamilies`: Gets product families associated with specific markets.
*   `/productfamily`: Gets details about a product family and lists products within that family.
*   `/productfamily/{productFamilyId}`: Gets details about a product family.
*   `/products`: Gets a list of products for a given market.
*   `/securityexchanges`: Gets the list of securityexchanges.
*   `/syntheticinstruments`: Gets a list of synthetic instruments.

---

### Known `ttmonitor` (Trade Monitor Service) Endpoints

Based on the TT REST API documentation UI, the following GET & POST endpoints are available under `https://ttrestapi.trade.tt/ttmonitor/<env>/` (all require `requestId` query parameter and standard auth headers, POST may have specific body requirements):

*   `POST /adminfill`: Adds an administrative fill.
*   `GET /creditutilization`: Gets credit limit and credit utilization details for a given account.
*   `GET /position`: Gets positions based on today's fills for all or selected accounts associated with the application key.
*   `GET /position/{accountId}`: Gets positions for the provided `accountId` based on today's fills.
*   `GET /productfamilyposition`: Gets positions based on today's fills aggregated by specific a product.
*   `GET /productfamilyposition/{accountId}`: Gets positions for the provided `accountId` based on today's fills.
*   `GET /productposition`: Gets positions based on today's fills aggregated by specific a product.
*   `GET /productposition/{accountId}`: Gets positions for the provided `accountId` based on today's fills.
*   `GET /sod/{accountId}`: Gets SODs for a given account ID.
*   `POST /sod/upload`: Requests a URL for uploading SODs.
*   `GET /sod/upload/{batchId}`: Provides the status of an SOD upload.

---

### Known `ttledger` (Ledger Service) Endpoints

Based on the TT REST API documentation UI, the following GET endpoints are available under `https://ttrestapi.trade.tt/ttledger/<env>/` (all require `requestId` query parameter and standard auth headers):

*   `GET /fills`: Retrieves fills for all users on accounts to which the application key has viewing and trading permissions.
*   `GET /orderdata`: Retrieves definitions for order-related enumerated values.
*   `GET /orders`: Retrieves working orders based on the user's ID and accounts.
*   `GET /orders/{orderId}`: Retrieves detailed information about a single working order.
*   `GET /positionmodifications`: Retrieves position modifications, such as start-of-day (SOC) records and manual fills.
*   `GET /tcrfills`: Retrieves trade capture fills (internal and external) for all users on accounts to which the application key has viewing and trading permissions.
*   `GET /tradingaccountfills`: Retrieves fills for all users - limited to accounts for which the user of the application key has trading permissions.

---
