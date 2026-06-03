# Complete Declarative Programming Guide
### Every Pattern — Real Scenarios — Imperative vs Declarative

> 10 Chapters | 50+ Patterns | Real-world examples for each

---

## The 3 Rules
```
Rule 1: Checking WHAT something is       → Registry
Rule 2: Doing MULTIPLE things in order   → Pipeline  
Rule 3: Checking CONDITIONS for a value  → Rules as Data
```

---

# Chapter 1 — Registry Patterns (Full Depth)
> Every pattern: real-world scenario, imperative code, declarative code

---

## 1.1 Basic Key Registry
**Scenario:** HTTP request router that dispatches to handlers based on HTTP method

**Imperative**
```python
def handle_request(method, request):
    if method == "GET":
        user = db.find(request.params["id"])
        return {"status": 200, "data": user}
    elif method == "POST":
        user = db.create(request.body)
        return {"status": 201, "data": user}
    elif method == "PUT":
        user = db.update(request.params["id"], request.body)
        return {"status": 200, "data": user}
    elif method == "DELETE":
        db.delete(request.params["id"])
        return {"status": 204}
    else:
        return {"status": 405, "error": "method not allowed"}
```

**Declarative**
```python
class HttpRouter:
    _handlers = {}

    @classmethod
    def register(cls, method):
        def decorator(fn):
            cls._handlers[method] = fn
            return fn
        return decorator

    @classmethod
    def dispatch(cls, method, request):
        handler = cls._handlers.get(method, cls._handlers["*"])
        return handler(request)

@HttpRouter.register("GET")
def _(request):
    user = db.find(request.params["id"])
    return {"status": 200, "data": user}

@HttpRouter.register("POST")
def _(request):
    user = db.create(request.body)
    return {"status": 201, "data": user}

@HttpRouter.register("PUT")
def _(request):
    user = db.update(request.params["id"], request.body)
    return {"status": 200, "data": user}

@HttpRouter.register("DELETE")
def _(request):
    db.delete(request.params["id"])
    return {"status": 204}

@HttpRouter.register("*")
def _(request):
    return {"status": 405, "error": "method not allowed"}

HttpRouter.dispatch("GET", request)
```

---

## 1.2 Decorator Registry
**Scenario:** File export system — export data to CSV, Excel, PDF

**Imperative**
```python
def export_report(format, data, filename):
    if format == "csv":
        rows = [",".join(row) for row in data]
        content = "\n".join(rows)
        with open(f"{filename}.csv", "w") as f:
            f.write(content)
    elif format == "excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in data:
            ws.append(row)
        wb.save(f"{filename}.xlsx")
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        for row in data:
            pdf.cell(0, 10, " | ".join(row), ln=True)
        pdf.output(f"{filename}.pdf")
    else:
        raise ValueError(f"Unknown format: {format}")
```

**Declarative**
```python
class ExportRegistry:
    _exporters = {}

    @classmethod
    def register(cls, format):
        def decorator(exporter_class):
            cls._exporters[format] = exporter_class()
            return exporter_class
        return decorator

    @classmethod
    def export(cls, format, data, filename):
        exporter = cls._exporters.get(format, cls._exporters["default"])
        return exporter.run(data, filename)

@ExportRegistry.register("csv")
class CsvExporter:
    def run(self, data, filename):
        rows    = [",".join(row) for row in data]
        content = "\n".join(rows)
        with open(f"{filename}.csv", "w") as f:
            f.write(content)

@ExportRegistry.register("excel")
class ExcelExporter:
    def run(self, data, filename):
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in data:
            ws.append(row)
        wb.save(f"{filename}.xlsx")

@ExportRegistry.register("pdf")
class PdfExporter:
    def run(self, data, filename):
        pdf = FPDF()
        pdf.add_page()
        for row in data:
            pdf.cell(0, 10, " | ".join(row), ln=True)
        pdf.output(f"{filename}.pdf")

@ExportRegistry.register("default")
class NullExporter:
    def run(self, data, filename):
        raise ValueError(f"Unknown format for {filename}")

ExportRegistry.export("csv", data, "monthly_report")
```

---

## 1.3 Class-based Registry
**Scenario:** Storage system — save files to S3, GCS, or local disk

**Imperative**
```python
def upload_file(backend, file_path, content):
    if backend == "s3":
        s3_client = boto3.client("s3",
            aws_access_key_id=S3_KEY,
            aws_secret_access_key=S3_SECRET
        )
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_path,
            Body=content
        )
        return f"s3://{S3_BUCKET}/{file_path}"

    elif backend == "gcs":
        gcs_client  = storage.Client(credentials=GCS_CREDS)
        bucket      = gcs_client.bucket(GCS_BUCKET)
        blob        = bucket.blob(file_path)
        blob.upload_from_string(content)
        return f"gs://{GCS_BUCKET}/{file_path}"

    elif backend == "local":
        full_path = Path(LOCAL_ROOT) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(full_path)

    else:
        raise ValueError(f"Unknown backend: {backend}")
```

**Declarative**
```python
class StorageRegistry:
    _backends = {}

    @classmethod
    def register(cls, name):
        def decorator(backend_class):
            cls._backends[name] = backend_class()
            return backend_class
        return decorator

    @classmethod
    def upload(cls, backend, file_path, content):
        return cls._backends.get(backend, cls._backends["default"]).upload(file_path, content)

    @classmethod
    def download(cls, backend, file_path):
        return cls._backends.get(backend, cls._backends["default"]).download(file_path)

@StorageRegistry.register("s3")
class S3Backend:
    _client = boto3.client("s3",
        aws_access_key_id=S3_KEY,
        aws_secret_access_key=S3_SECRET
    )
    def upload(self, path, content):
        self._client.put_object(Bucket=S3_BUCKET, Key=path, Body=content)
        return f"s3://{S3_BUCKET}/{path}"
    def download(self, path):
        obj = self._client.get_object(Bucket=S3_BUCKET, Key=path)
        return obj["Body"].read()

@StorageRegistry.register("gcs")
class GCSBackend:
    _client = storage.Client(credentials=GCS_CREDS)
    def upload(self, path, content):
        bucket = self._client.bucket(GCS_BUCKET)
        blob   = bucket.blob(path)
        blob.upload_from_string(content)
        return f"gs://{GCS_BUCKET}/{path}"
    def download(self, path):
        bucket = self._client.bucket(GCS_BUCKET)
        return bucket.blob(path).download_as_bytes()

@StorageRegistry.register("local")
class LocalBackend:
    def upload(self, path, content):
        full = Path(LOCAL_ROOT) / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(content)
        return str(full)
    def download(self, path):
        return (Path(LOCAL_ROOT) / path).read_bytes()

@StorageRegistry.register("default")
class NullBackend:
    def upload(self, path, content): raise ValueError(f"Unknown storage backend")
    def download(self, path):        raise ValueError(f"Unknown storage backend")

StorageRegistry.upload("s3", "reports/2024/q1.pdf", pdf_bytes)
```

---

## 1.4 Fallback / Default Registry
**Scenario:** Message serializer with fallback to JSON when format unknown

**Imperative**
```python
def serialize_message(message, format):
    if format == "json":
        return json.dumps(message).encode()
    elif format == "msgpack":
        return msgpack.packb(message)
    elif format == "protobuf":
        msg = ProtoMessage()
        msg.ParseFromDict(message)
        return msg.SerializeToString()
    else:
        # silent fallback — dangerous, no one knows this happened
        return json.dumps(message).encode()

def deserialize_message(data, format):
    if format == "json":
        return json.loads(data)
    elif format == "msgpack":
        return msgpack.unpackb(data)
    elif format == "protobuf":
        msg = ProtoMessage()
        msg.ParseFromString(data)
        return MessageToDict(msg)
    else:
        return json.loads(data)
```

**Declarative**
```python
class SerializerRegistry:
    _serializers = {}
    _default     = "json"

    @classmethod
    def register(cls, format, default=False):
        def decorator(serializer_class):
            cls._serializers[format] = serializer_class()
            if default:
                cls._default = format
            return serializer_class
        return decorator

    @classmethod
    def serialize(cls, message, format):
        return cls._serializers.get(
            format, cls._serializers[cls._default]
        ).encode(message)

    @classmethod
    def deserialize(cls, data, format):
        return cls._serializers.get(
            format, cls._serializers[cls._default]
        ).decode(data)

@SerializerRegistry.register("json", default=True)
class JsonSerializer:
    def encode(self, msg): return json.dumps(msg).encode()
    def decode(self, data): return json.loads(data)

@SerializerRegistry.register("msgpack")
class MsgpackSerializer:
    def encode(self, msg): return msgpack.packb(msg)
    def decode(self, data): return msgpack.unpackb(data)

@SerializerRegistry.register("protobuf")
class ProtobufSerializer:
    def encode(self, msg):
        proto = ProtoMessage()
        proto.ParseFromDict(msg)
        return proto.SerializeToString()
    def decode(self, data):
        proto = ProtoMessage()
        proto.ParseFromString(data)
        return MessageToDict(proto)

SerializerRegistry.serialize(message, "msgpack")
SerializerRegistry.deserialize(data, "unknown_format")  # falls back to json
```

---

## 1.5 Nested Registry
**Scenario:** REST API handler — dispatch by resource + action

**Imperative**
```python
def handle_api(resource, action, payload):
    if resource == "users":
        if action == "create":
            validate_user(payload)
            user = User(**payload)
            db.save(user)
            return {"id": user.id, "status": "created"}
        elif action == "update":
            user = db.find_user(payload["id"])
            user.update(**payload)
            db.save(user)
            return {"id": user.id, "status": "updated"}
        elif action == "delete":
            db.delete_user(payload["id"])
            return {"status": "deleted"}
    elif resource == "orders":
        if action == "create":
            validate_order(payload)
            order = Order(**payload)
            db.save(order)
            charge_card(order)
            return {"id": order.id, "status": "created"}
        elif action == "cancel":
            order = db.find_order(payload["id"])
            order.cancel()
            refund_card(order)
            return {"id": order.id, "status": "cancelled"}
    elif resource == "products":
        if action == "create":
            product = Product(**payload)
            db.save(product)
            index_search(product)
            return {"id": product.id, "status": "created"}
```

**Declarative**
```python
class ApiRegistry:
    _registry = {}

    @classmethod
    def register(cls, resource, action):
        def decorator(handler_class):
            cls._registry.setdefault(resource, {})[action] = handler_class()
            return handler_class
        return decorator

    @classmethod
    def handle(cls, resource, action, payload):
        resource_handlers = cls._registry.get(resource, {})
        handler           = resource_handlers.get(action, UnknownActionHandler())
        return handler.execute(payload)

class UnknownActionHandler:
    def execute(self, payload):
        raise ValueError("Unknown resource or action")

@ApiRegistry.register("users", "create")
class CreateUserHandler:
    def execute(self, payload):
        validate_user(payload)
        user = User(**payload)
        db.save(user)
        return {"id": user.id, "status": "created"}

@ApiRegistry.register("users", "update")
class UpdateUserHandler:
    def execute(self, payload):
        user = db.find_user(payload["id"])
        user.update(**payload)
        db.save(user)
        return {"id": user.id, "status": "updated"}

@ApiRegistry.register("users", "delete")
class DeleteUserHandler:
    def execute(self, payload):
        db.delete_user(payload["id"])
        return {"status": "deleted"}

@ApiRegistry.register("orders", "create")
class CreateOrderHandler:
    def execute(self, payload):
        validate_order(payload)
        order = Order(**payload)
        db.save(order)
        charge_card(order)
        return {"id": order.id, "status": "created"}

@ApiRegistry.register("orders", "cancel")
class CancelOrderHandler:
    def execute(self, payload):
        order = db.find_order(payload["id"])
        order.cancel()
        refund_card(order)
        return {"id": order.id, "status": "cancelled"}

@ApiRegistry.register("products", "create")
class CreateProductHandler:
    def execute(self, payload):
        product = Product(**payload)
        db.save(product)
        index_search(product)
        return {"id": product.id, "status": "created"}

ApiRegistry.handle("orders", "create", payload)
```

---

## 1.6 Priority Registry
**Scenario:** Pricing engine — VIP discount beats coupon beats sale

**Imperative**
```python
def get_final_price(product, user, cart):
    # Order matters — easy to get wrong, hard to change
    if user.tier == "diamond":
        base = product.price * 0.60
    elif user.tier == "platinum":
        base = product.price * 0.70
    elif user.tier == "gold":
        base = product.price * 0.80
    elif user.has_coupon and user.coupon.type == "percentage":
        base = product.price * (1 - user.coupon.value)
    elif user.has_coupon and user.coupon.type == "fixed":
        base = product.price - user.coupon.value
    elif product.on_sale:
        base = product.sale_price
    elif cart.total > 200:
        base = product.price * 0.95
    else:
        base = product.price
    return max(base, 0)
```

**Declarative**
```python
class PricingRegistry:
    _rules = []

    @classmethod
    def rule(cls, priority):
        def decorator(rule_class):
            cls._rules.append((priority, rule_class()))
            cls._rules.sort(key=lambda x: x[0], reverse=True)
            return rule_class
        return decorator

    @classmethod
    def calculate(cls, product, user, cart):
        for _, rule in cls._rules:
            if rule.matches(product, user, cart):
                return max(rule.apply(product, user, cart), 0)
        return product.price

@PricingRegistry.rule(priority=1000)
class DiamondTierPricing:
    def matches(self, p, u, c): return u.tier == "diamond"
    def apply(self, p, u, c):   return p.price * 0.60

@PricingRegistry.rule(priority=900)
class PlatinumTierPricing:
    def matches(self, p, u, c): return u.tier == "platinum"
    def apply(self, p, u, c):   return p.price * 0.70

@PricingRegistry.rule(priority=800)
class GoldTierPricing:
    def matches(self, p, u, c): return u.tier == "gold"
    def apply(self, p, u, c):   return p.price * 0.80

@PricingRegistry.rule(priority=500)
class PercentageCouponPricing:
    def matches(self, p, u, c): return u.has_coupon and u.coupon.type == "percentage"
    def apply(self, p, u, c):   return p.price * (1 - u.coupon.value)

@PricingRegistry.rule(priority=500)
class FixedCouponPricing:
    def matches(self, p, u, c): return u.has_coupon and u.coupon.type == "fixed"
    def apply(self, p, u, c):   return p.price - u.coupon.value

@PricingRegistry.rule(priority=200)
class SalePricing:
    def matches(self, p, u, c): return p.on_sale
    def apply(self, p, u, c):   return p.sale_price

@PricingRegistry.rule(priority=100)
class BulkCartPricing:
    def matches(self, p, u, c): return c.total > 200
    def apply(self, p, u, c):   return p.price * 0.95

PricingRegistry.calculate(product, user, cart)
```

---

## 1.7 Multi-key Registry
**Scenario:** Tax rate lookup by country code

**Imperative**
```python
def get_tax_rate(country_code):
    if country_code in ["US-CA", "US-NY", "US-TX"]:
        rates = {"US-CA": 0.0725, "US-NY": 0.08, "US-TX": 0.0625}
        return rates[country_code]
    elif country_code in ["GB", "UK"]:
        return 0.20
    elif country_code in ["DE", "AT", "FR"]:
        return 0.19
    elif country_code in ["AU", "NZ"]:
        return 0.10
    else:
        return 0.0
```

**Declarative**
```python
class TaxRegistry:
    _rates = {}

    @classmethod
    def register(cls, rate, *country_codes):
        def decorator(fn):
            for code in country_codes:
                cls._rates[code] = rate
            return fn
        return decorator

    @classmethod
    def get_rate(cls, country_code):
        return cls._rates.get(country_code, 0.0)

@TaxRegistry.register(0.0725, "US-CA")
def _(): pass

@TaxRegistry.register(0.08, "US-NY")
def _(): pass

@TaxRegistry.register(0.0625, "US-TX")
def _(): pass

@TaxRegistry.register(0.20, "GB", "UK")
def _(): pass

@TaxRegistry.register(0.19, "DE", "AT", "FR")
def _(): pass

@TaxRegistry.register(0.10, "AU", "NZ")
def _(): pass

TaxRegistry.get_rate("DE")
```

---

## 1.8 Lazy Registry
**Scenario:** Database connection pool — create connection only when first needed

**Imperative**
```python
_connections = {}

def get_db_connection(db_name):
    if db_name == "primary":
        if "primary" not in _connections:
            _connections["primary"] = psycopg2.connect(
                host=PRIMARY_HOST, port=5432,
                user=DB_USER, password=DB_PASS,
                dbname="primary_db"
            )
        return _connections["primary"]

    elif db_name == "replica":
        if "replica" not in _connections:
            _connections["replica"] = psycopg2.connect(
                host=REPLICA_HOST, port=5432,
                user=DB_USER, password=DB_PASS,
                dbname="primary_db"
            )
        return _connections["replica"]

    elif db_name == "analytics":
        if "analytics" not in _connections:
            _connections["analytics"] = psycopg2.connect(
                host=ANALYTICS_HOST, port=5432,
                user=DB_USER, password=DB_PASS,
                dbname="analytics_db"
            )
        return _connections["analytics"]
```

**Declarative**
```python
class ConnectionRegistry:
    _factories  = {}
    _instances  = {}

    @classmethod
    def register(cls, name):
        def decorator(factory_fn):
            cls._factories[name] = factory_fn
            return factory_fn
        return decorator

    @classmethod
    def get(cls, name):
        if name not in cls._instances:
            factory = cls._factories.get(name)
            if factory is None:
                raise ValueError(f"Unknown database: {name}")
            cls._instances[name] = factory()
        return cls._instances[name]

    @classmethod
    def reset(cls, name=None):
        if name:
            cls._instances.pop(name, None)
        else:
            cls._instances.clear()

@ConnectionRegistry.register("primary")
def _():
    return psycopg2.connect(
        host=PRIMARY_HOST, port=5432,
        user=DB_USER, password=DB_PASS,
        dbname="primary_db"
    )

@ConnectionRegistry.register("replica")
def _():
    return psycopg2.connect(
        host=REPLICA_HOST, port=5432,
        user=DB_USER, password=DB_PASS,
        dbname="primary_db"
    )

@ConnectionRegistry.register("analytics")
def _():
    return psycopg2.connect(
        host=ANALYTICS_HOST, port=5432,
        user=DB_USER, password=DB_PASS,
        dbname="analytics_db"
    )

conn = ConnectionRegistry.get("primary")
```

---

## 1.9 Scoped Registry
**Scenario:** Feature flags per tenant with different configurations

**Imperative**
```python
def is_feature_enabled(tenant_id, feature_name):
    if tenant_id == "acme_corp":
        if feature_name == "new_dashboard":
            return True
        elif feature_name == "ai_recommendations":
            return True
        elif feature_name == "bulk_export":
            return False
    elif tenant_id == "globex":
        if feature_name == "new_dashboard":
            return False
        elif feature_name == "ai_recommendations":
            return False
        elif feature_name == "bulk_export":
            return True
    elif tenant_id == "initech":
        if feature_name == "new_dashboard":
            return True
        elif feature_name == "ai_recommendations":
            return False
        elif feature_name == "bulk_export":
            return True
    return False
```

**Declarative**
```python
class TenantFeatureRegistry:
    _tenants = {}

    @classmethod
    def register(cls, tenant_id):
        def decorator(config_class):
            cls._tenants[tenant_id] = config_class()
            return config_class
        return decorator

    @classmethod
    def is_enabled(cls, tenant_id, feature):
        tenant = cls._tenants.get(tenant_id, cls._tenants["default"])
        return tenant.is_enabled(feature)

class BaseConfig:
    _features = {}
    def is_enabled(self, feature):
        return self._features.get(feature, False)

@TenantFeatureRegistry.register("acme_corp")
class AcmeConfig(BaseConfig):
    _features = {
        "new_dashboard":       True,
        "ai_recommendations":  True,
        "bulk_export":         False,
    }

@TenantFeatureRegistry.register("globex")
class GlobexConfig(BaseConfig):
    _features = {
        "new_dashboard":       False,
        "ai_recommendations":  False,
        "bulk_export":         True,
    }

@TenantFeatureRegistry.register("initech")
class InitechConfig(BaseConfig):
    _features = {
        "new_dashboard":       True,
        "ai_recommendations":  False,
        "bulk_export":         True,
    }

@TenantFeatureRegistry.register("default")
class DefaultConfig(BaseConfig):
    _features = {}

TenantFeatureRegistry.is_enabled("acme_corp", "ai_recommendations")
```

---

## 1.10 Plugin Registry
**Scenario:** Webhook event processor where each event type is a separate plugin

**Imperative**
```python
# core/webhook.py — modified every time a new event is added
def process_webhook(event_type, payload, headers):
    if event_type == "payment.completed":
        order_id = payload["order_id"]
        amount   = payload["amount"]
        order    = db.get_order(order_id)
        order.mark_paid(amount)
        db.save(order)
        send_receipt_email(order)

    elif event_type == "payment.failed":
        order_id = payload["order_id"]
        reason   = payload["failure_reason"]
        order    = db.get_order(order_id)
        order.mark_failed(reason)
        db.save(order)
        notify_customer_of_failure(order)

    elif event_type == "subscription.cancelled":
        sub_id = payload["subscription_id"]
        sub    = db.get_subscription(sub_id)
        sub.cancel()
        db.save(sub)
        send_cancellation_email(sub)

    elif event_type == "refund.processed":
        refund_id = payload["refund_id"]
        refund    = db.get_refund(refund_id)
        refund.mark_complete()
        db.save(refund)
        send_refund_confirmation(refund)

    else:
        logger.warning(f"Unhandled webhook event: {event_type}")
```

**Declarative**
```python
# core/webhook.py — never changes
class WebhookRegistry:
    _handlers = {}

    @classmethod
    def handles(cls, event_type):
        def decorator(handler_class):
            cls._handlers[event_type] = handler_class()
            return handler_class
        return decorator

    @classmethod
    def process(cls, event_type, payload, headers):
        handler = cls._handlers.get(event_type, cls._handlers["*"])
        return handler.handle(payload, headers)

@WebhookRegistry.handles("*")
class UnknownEventHandler:
    def handle(self, payload, headers):
        logger.warning(f"Unhandled webhook: {payload}")


# handlers/payment_completed.py — completely separate file
@WebhookRegistry.handles("payment.completed")
class PaymentCompletedHandler:
    def handle(self, payload, headers):
        order = db.get_order(payload["order_id"])
        order.mark_paid(payload["amount"])
        db.save(order)
        send_receipt_email(order)


# handlers/payment_failed.py — completely separate file
@WebhookRegistry.handles("payment.failed")
class PaymentFailedHandler:
    def handle(self, payload, headers):
        order = db.get_order(payload["order_id"])
        order.mark_failed(payload["failure_reason"])
        db.save(order)
        notify_customer_of_failure(order)


# handlers/subscription_cancelled.py — completely separate file
@WebhookRegistry.handles("subscription.cancelled")
class SubscriptionCancelledHandler:
    def handle(self, payload, headers):
        sub = db.get_subscription(payload["subscription_id"])
        sub.cancel()
        db.save(sub)
        send_cancellation_email(sub)


# handlers/refund_processed.py — completely separate file
@WebhookRegistry.handles("refund.processed")
class RefundProcessedHandler:
    def handle(self, payload, headers):
        refund = db.get_refund(payload["refund_id"])
        refund.mark_complete()
        db.save(refund)
        send_refund_confirmation(refund)


WebhookRegistry.process("payment.completed", payload, headers)
```
# Chapter 2 — Pipeline Patterns (Full Depth)
> Every pattern: real-world scenario, imperative code, declarative code

---

## 2.1 Linear Pipeline
**Scenario:** User registration — normalize, validate, enrich, save

**Imperative**
```python
def register_user(raw_input):
    # normalize
    raw_input["email"] = raw_input["email"].lower().strip()
    raw_input["name"]  = raw_input["name"].strip().title()
    raw_input["phone"] = re.sub(r"\D", "", raw_input["phone"])

    # validate
    if not raw_input["email"] or "@" not in raw_input["email"]:
        raise ValidationError("invalid email")
    if len(raw_input["name"]) < 2:
        raise ValidationError("name too short")
    if len(raw_input["phone"]) != 10:
        raise ValidationError("invalid phone")

    # enrich
    raw_input["gravatar"] = hashlib.md5(raw_input["email"].encode()).hexdigest()
    raw_input["slug"]     = raw_input["name"].lower().replace(" ", "-")
    raw_input["created"]  = datetime.utcnow().isoformat()

    # save
    user = db.insert("users", raw_input)
    cache.set(f"user:{user.id}", user)
    search_index.add(user)

    return user
```

**Declarative**
```python
class UserRegistrationPipeline:
    _stages = []

    @classmethod
    def stage(cls, fn):
        cls._stages.append(fn)
        return fn

    @classmethod
    def run(cls, raw_input):
        return reduce(lambda data, stage: stage(data), cls._stages, raw_input)

@UserRegistrationPipeline.stage
def normalize(data):
    return {
        **data,
        "email": data["email"].lower().strip(),
        "name":  data["name"].strip().title(),
        "phone": re.sub(r"\D", "", data["phone"]),
    }

@UserRegistrationPipeline.stage
def validate(data):
    if not data["email"] or "@" not in data["email"]:
        raise ValidationError("invalid email")
    if len(data["name"]) < 2:
        raise ValidationError("name too short")
    if len(data["phone"]) != 10:
        raise ValidationError("invalid phone")
    return data

@UserRegistrationPipeline.stage
def enrich(data):
    return {
        **data,
        "gravatar": hashlib.md5(data["email"].encode()).hexdigest(),
        "slug":     data["name"].lower().replace(" ", "-"),
        "created":  datetime.utcnow().isoformat(),
    }

@UserRegistrationPipeline.stage
def persist(data):
    user = db.insert("users", data)
    cache.set(f"user:{user.id}", user)
    search_index.add(user)
    return user

UserRegistrationPipeline.run(raw_input)
```

---

## 2.2 Branching Pipeline
**Scenario:** Order processing — digital, physical, subscription each have different steps

**Imperative**
```python
def process_order(order):
    # shared validation
    if not order.user_id:
        raise ValidationError("user required")
    if order.amount <= 0:
        raise ValidationError("amount must be positive")
    if not order.payment_method:
        raise ValidationError("payment method required")

    # charge is shared
    charge_result = stripe.charge(order.payment_method, order.amount)
    order.charge_id = charge_result.id

    # branch per type
    if order.type == "digital":
        license_key        = generate_license(order.product_id)
        download_url       = create_download_link(order.product_id)
        order.license_key  = license_key
        order.download_url = download_url
        send_digital_delivery_email(order)

    elif order.type == "physical":
        warehouse_order = create_warehouse_order(order)
        tracking_number = assign_carrier(warehouse_order)
        order.tracking  = tracking_number
        send_shipping_confirmation(order)

    elif order.type == "subscription":
        sub             = create_subscription(order)
        order.sub_id    = sub.id
        order.next_bill = sub.next_billing_date
        send_subscription_welcome(order)

    else:
        raise ValueError(f"Unknown order type: {order.type}")

    db.save(order)
    return order
```

**Declarative**
```python
class OrderPipeline:
    _shared_stages = []
    _branches      = {}

    @classmethod
    def shared(cls, fn):
        cls._shared_stages.append(fn)
        return fn

    @classmethod
    def branch(cls, order_type):
        def decorator(pipeline_class):
            cls._branches[order_type] = pipeline_class()
            return pipeline_class
        return decorator

    @classmethod
    def run(cls, order):
        after_shared = reduce(
            lambda o, stage: stage(o),
            cls._shared_stages,
            order
        )
        branch = cls._branches.get(order.type, UnknownOrderBranch())
        result = branch.run(after_shared)
        return persist_order(result)

class UnknownOrderBranch:
    def run(self, order):
        raise ValueError(f"Unknown order type: {order.type}")

@OrderPipeline.shared
def validate(order):
    if not order.user_id:       raise ValidationError("user required")
    if order.amount <= 0:       raise ValidationError("amount must be positive")
    if not order.payment_method: raise ValidationError("payment method required")
    return order

@OrderPipeline.shared
def charge(order):
    result = stripe.charge(order.payment_method, order.amount)
    return replace(order, charge_id=result.id)

@OrderPipeline.branch("digital")
class DigitalOrderBranch:
    def run(self, order):
        license_key  = generate_license(order.product_id)
        download_url = create_download_link(order.product_id)
        enriched     = replace(order,
            license_key=license_key,
            download_url=download_url
        )
        send_digital_delivery_email(enriched)
        return enriched

@OrderPipeline.branch("physical")
class PhysicalOrderBranch:
    def run(self, order):
        warehouse_order = create_warehouse_order(order)
        tracking        = assign_carrier(warehouse_order)
        enriched        = replace(order, tracking=tracking)
        send_shipping_confirmation(enriched)
        return enriched

@OrderPipeline.branch("subscription")
class SubscriptionOrderBranch:
    def run(self, order):
        sub      = create_subscription(order)
        enriched = replace(order, sub_id=sub.id, next_bill=sub.next_billing_date)
        send_subscription_welcome(enriched)
        return enriched

OrderPipeline.run(order)
```

---

## 2.3 Async Pipeline
**Scenario:** API request lifecycle — auth, rate limit, validate, execute, log

**Imperative**
```python
async def handle_api_request(request):
    # auth
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response(401, {"error": "missing token"})
    user = await auth_service.verify_token(token)
    if not user:
        return Response(401, {"error": "invalid token"})

    # rate limit
    key     = f"rate:{user.id}:{request.path}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    if current > user.rate_limit:
        return Response(429, {"error": "rate limit exceeded"})

    # validate
    schema = get_schema(request.path, request.method)
    errors = validate_against_schema(request.body, schema)
    if errors:
        return Response(400, {"errors": errors})

    # execute
    handler = get_handler(request.path, request.method)
    result  = await handler(request, user)

    # log
    await audit_log.record(
        user_id=user.id,
        action=f"{request.method} {request.path}",
        result=result.status
    )

    return result
```

**Declarative**
```python
class AsyncRequestPipeline:
    _stages = []

    @classmethod
    def stage(cls, fn):
        cls._stages.append(fn)
        return fn

    @classmethod
    async def run(cls, request):
        context = RequestContext(request=request)
        for stage in cls._stages:
            context = await stage(context)
            if context.response:       # short-circuit if response set
                return context.response
        return context.response

@AsyncRequestPipeline.stage
async def authenticate(ctx):
    token = ctx.request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return ctx.with_response(Response(401, {"error": "missing token"}))
    user = await auth_service.verify_token(token)
    if not user:
        return ctx.with_response(Response(401, {"error": "invalid token"}))
    return ctx.with_user(user)

@AsyncRequestPipeline.stage
async def rate_limit(ctx):
    key     = f"rate:{ctx.user.id}:{ctx.request.path}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    if current > ctx.user.rate_limit:
        return ctx.with_response(Response(429, {"error": "rate limit exceeded"}))
    return ctx

@AsyncRequestPipeline.stage
async def validate_body(ctx):
    schema = get_schema(ctx.request.path, ctx.request.method)
    errors = validate_against_schema(ctx.request.body, schema)
    if errors:
        return ctx.with_response(Response(400, {"errors": errors}))
    return ctx

@AsyncRequestPipeline.stage
async def execute(ctx):
    handler  = get_handler(ctx.request.path, ctx.request.method)
    response = await handler(ctx.request, ctx.user)
    return ctx.with_response(response)

@AsyncRequestPipeline.stage
async def audit(ctx):
    await audit_log.record(
        user_id=ctx.user.id,
        action=f"{ctx.request.method} {ctx.request.path}",
        result=ctx.response.status
    )
    return ctx

await AsyncRequestPipeline.run(request)
```

---

## 2.4 Pipeline with Rollback
**Scenario:** Payment processing — reserve, charge, fulfill; rollback on any failure

**Imperative**
```python
def process_payment(order):
    inventory_reserved = False
    payment_charged    = False
    fulfillment_done   = False

    try:
        # step 1
        reserve_result     = inventory.reserve(order.items)
        inventory_reserved = True

        # step 2
        charge_result   = stripe.charge(order.payment_method, order.amount)
        payment_charged = True
        order.charge_id = charge_result.id

        # step 3
        fulfillment     = fulfillment_service.create(order)
        fulfillment_done = True
        order.fulfillment_id = fulfillment.id

        db.save(order)
        return order

    except Exception as e:
        if fulfillment_done:
            fulfillment_service.cancel(order.fulfillment_id)
        if payment_charged:
            stripe.refund(order.charge_id)
        if inventory_reserved:
            inventory.release(reserve_result.reservation_id)
        raise PaymentProcessingError(str(e))
```

**Declarative**
```python
class RollbackPipeline:
    _stages = []

    @classmethod
    def stage(cls, fn=None):
        def decorator(stage_class):
            cls._stages.append(stage_class())
            return stage_class
        return decorator

    @classmethod
    def run(cls, data):
        completed = []
        try:
            result = data
            for stage in cls._stages:
                result = stage.execute(result)
                completed.append((stage, result))
            return result
        except Exception as e:
            for stage, state in reversed(completed):
                try:
                    stage.rollback(state)
                except Exception as rollback_err:
                    logger.error(f"Rollback failed: {rollback_err}")
            raise PaymentProcessingError(str(e))

@RollbackPipeline.stage()
class ReserveInventoryStage:
    def execute(self, order):
        result = inventory.reserve(order.items)
        return replace(order, reservation_id=result.reservation_id)
    def rollback(self, order):
        inventory.release(order.reservation_id)

@RollbackPipeline.stage()
class ChargePaymentStage:
    def execute(self, order):
        result = stripe.charge(order.payment_method, order.amount)
        return replace(order, charge_id=result.id)
    def rollback(self, order):
        stripe.refund(order.charge_id)

@RollbackPipeline.stage()
class CreateFulfillmentStage:
    def execute(self, order):
        fulfillment = fulfillment_service.create(order)
        return replace(order, fulfillment_id=fulfillment.id)
    def rollback(self, order):
        fulfillment_service.cancel(order.fulfillment_id)

@RollbackPipeline.stage()
class PersistOrderStage:
    def execute(self, order):
        db.save(order)
        return order
    def rollback(self, order):
        db.delete(order.id)

RollbackPipeline.run(order)
```

---

## 2.5 Conditional Stage Pipeline
**Scenario:** Data export pipeline — some stages only run based on config

**Imperative**
```python
def export_data(records, config):
    result = records

    # always normalize
    normalized = []
    for r in result:
        normalized.append(normalize_record(r))
    result = normalized

    # only if dedup enabled
    if config.get("deduplicate"):
        seen   = set()
        deduped = []
        for r in result:
            key = r["id"]
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        result = deduped

    # always transform
    transformed = []
    for r in result:
        transformed.append(transform_record(r))
    result = transformed

    # only if enrichment enabled
    if config.get("enrich"):
        enriched = []
        for r in result:
            extra = fetch_enrichment(r["id"])
            enriched.append({**r, **extra})
        result = enriched

    # only if compression enabled
    if config.get("compress"):
        result = gzip.compress(json.dumps(result).encode())

    return result
```

**Declarative**
```python
class ConditionalPipeline:
    _stages = []

    @classmethod
    def stage(cls, condition_key=None):
        def decorator(fn):
            cls._stages.append((condition_key, fn))
            return fn
        return decorator

    @classmethod
    def run(cls, data, config):
        active = [
            fn for key, fn in cls._stages
            if key is None or config.get(key)
        ]
        return reduce(lambda d, fn: fn(d), active, data)

@ConditionalPipeline.stage()
def normalize(records):
    return [normalize_record(r) for r in records]

@ConditionalPipeline.stage(condition_key="deduplicate")
def deduplicate(records):
    seen = set()
    return [
        r for r in records
        if r["id"] not in seen and not seen.add(r["id"])
    ]

@ConditionalPipeline.stage()
def transform(records):
    return [transform_record(r) for r in records]

@ConditionalPipeline.stage(condition_key="enrich")
def enrich(records):
    return [{**r, **fetch_enrichment(r["id"])} for r in records]

@ConditionalPipeline.stage(condition_key="compress")
def compress(records):
    return gzip.compress(json.dumps(records).encode())

ConditionalPipeline.run(records, config={"deduplicate": True, "enrich": True})
```

---

## 2.6 Parallel Pipeline
**Scenario:** Dashboard loader — fetch all widgets concurrently

**Imperative**
```python
async def load_dashboard(user_id, dashboard_id):
    # all sequential — each waits for previous
    profile       = await fetch_user_profile(user_id)
    orders        = await fetch_recent_orders(user_id)
    notifications = await fetch_notifications(user_id)
    analytics     = await fetch_analytics(user_id, dashboard_id)
    recommendations = await fetch_recommendations(user_id)
    alerts        = await fetch_alerts(user_id)

    return {
        "profile":         profile,
        "orders":          orders,
        "notifications":   notifications,
        "analytics":       analytics,
        "recommendations": recommendations,
        "alerts":          alerts,
    }
```

**Declarative**
```python
class DashboardLoader:
    _widgets = {}

    @classmethod
    def widget(cls, name):
        def decorator(fn):
            cls._widgets[name] = fn
            return fn
        return decorator

    @classmethod
    async def load(cls, context):
        results = await asyncio.gather(*[
            fn(context) for fn in cls._widgets.values()
        ], return_exceptions=True)

        return {
            name: result if not isinstance(result, Exception) else None
            for name, result in zip(cls._widgets.keys(), results)
        }

@DashboardLoader.widget("profile")
async def _(ctx): return await fetch_user_profile(ctx.user_id)

@DashboardLoader.widget("orders")
async def _(ctx): return await fetch_recent_orders(ctx.user_id)

@DashboardLoader.widget("notifications")
async def _(ctx): return await fetch_notifications(ctx.user_id)

@DashboardLoader.widget("analytics")
async def _(ctx): return await fetch_analytics(ctx.user_id, ctx.dashboard_id)

@DashboardLoader.widget("recommendations")
async def _(ctx): return await fetch_recommendations(ctx.user_id)

@DashboardLoader.widget("alerts")
async def _(ctx): return await fetch_alerts(ctx.user_id)

await DashboardLoader.load(context)
```

---

## 2.7 Streaming Pipeline
**Scenario:** Process a large log file — parse, filter errors, extract fields, write report

**Imperative**
```python
def process_log_file(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()      # entire file in RAM

    errors = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("level") != "ERROR":
            continue
        if not record.get("service") or not record.get("message"):
            continue
        errors.append({
            "timestamp": record["timestamp"],
            "service":   record["service"],
            "message":   record["message"],
            "trace_id":  record.get("trace_id", ""),
        })

    with open(output_path, "w") as f:
        for error in errors:
            f.write(json.dumps(error) + "\n")
```

**Declarative**
```python
class LogStreamPipeline:
    _stages = []

    @classmethod
    def stage(cls, fn):
        cls._stages.append(fn)
        return fn

    @classmethod
    def run(cls, source):
        return reduce(lambda stream, fn: fn(stream), cls._stages, source)

def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

@LogStreamPipeline.stage
def skip_empty(lines):
    return (line for line in lines if line)

@LogStreamPipeline.stage
def parse_json(lines):
    for line in lines:
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue

@LogStreamPipeline.stage
def filter_errors(records):
    return (r for r in records if r.get("level") == "ERROR")

@LogStreamPipeline.stage
def filter_complete(records):
    return (r for r in records if r.get("service") and r.get("message"))

@LogStreamPipeline.stage
def extract_fields(records):
    return (
        {
            "timestamp": r["timestamp"],
            "service":   r["service"],
            "message":   r["message"],
            "trace_id":  r.get("trace_id", ""),
        }
        for r in records
    )

def write_output(stream, output_path):
    with open(output_path, "w") as f:
        for record in stream:
            f.write(json.dumps(record) + "\n")

write_output(LogStreamPipeline.run(read_lines(input_path)), output_path)
```

---

## 2.8 Middleware Pipeline
**Scenario:** Express-style middleware — auth, logging, compression, CORS

**Imperative**
```python
def handle(request):
    # CORS
    if request.method == "OPTIONS":
        return Response(200, headers={
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE",
        })

    # auth
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response(401, {"error": "unauthorized"})
    user = verify_token(token)
    if not user:
        return Response(401, {"error": "invalid token"})
    request.user = user

    # logging
    start   = time.time()
    logger.info(f"[{request.method}] {request.path} started")

    # execute
    response = route_and_execute(request)

    # logging end
    duration = time.time() - start
    logger.info(f"[{request.method}] {request.path} {response.status} {duration:.2f}s")

    # compression
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        response.body    = gzip.compress(response.body)
        response.headers["Content-Encoding"] = "gzip"

    return response
```

**Declarative**
```python
class MiddlewareStack:
    _middlewares = []

    @classmethod
    def use(cls, fn):
        cls._middlewares.append(fn)
        return fn

    @classmethod
    def handle(cls, request):
        def build_chain(middlewares, final):
            if not middlewares:
                return final
            head, *tail = middlewares
            next_handler = build_chain(tail, final)
            return lambda req: head(req, next_handler)
        return build_chain(cls._middlewares, route_and_execute)(request)

@MiddlewareStack.use
def cors(request, next):
    if request.method == "OPTIONS":
        return Response(200, headers={
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE",
        })
    return next(request)

@MiddlewareStack.use
def authenticate(request, next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response(401, {"error": "unauthorized"})
    user = verify_token(token)
    if not user:
        return Response(401, {"error": "invalid token"})
    return next(request.with_user(user))

@MiddlewareStack.use
def logger_mw(request, next):
    start    = time.time()
    logger.info(f"[{request.method}] {request.path} started")
    response = next(request)
    duration = time.time() - start
    logger.info(f"[{request.method}] {request.path} {response.status} {duration:.2f}s")
    return response

@MiddlewareStack.use
def compression(request, next):
    response = next(request)
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        response.body = gzip.compress(response.body)
        response.headers["Content-Encoding"] = "gzip"
    return response

MiddlewareStack.handle(request)
```

---

## 2.9 Retry Pipeline
**Scenario:** Data sync pipeline — each stage retries independently on failure

**Imperative**
```python
def sync_data(source_id):
    # fetch with retry
    data = None
    for attempt in range(3):
        try:
            data = fetch_from_source(source_id)
            break
        except TransientError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

    # transform with retry
    transformed = None
    for attempt in range(2):
        try:
            transformed = transform_data(data)
            break
        except TransientError:
            if attempt == 1:
                raise
            time.sleep(1)

    # push with retry
    for attempt in range(5):
        try:
            push_to_destination(transformed)
            break
        except TransientError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)

    return transformed
```

**Declarative**
```python
class RetryPipeline:
    _stages = []

    @classmethod
    def stage(cls, attempts=3, backoff=2):
        def decorator(stage_class):
            cls._stages.append(stage_class(attempts, backoff))
            return stage_class
        return decorator

    @classmethod
    def run(cls, data):
        return reduce(lambda d, stage: stage.execute(d), cls._stages, data)

class RetryableStage:
    def __init__(self, attempts, backoff):
        self._attempts = attempts
        self._backoff  = backoff

    def execute(self, data):
        last_error = None
        for attempt in range(self._attempts):
            try:
                return self.process(data)
            except TransientError as e:
                last_error = e
                time.sleep(self._backoff ** attempt)
        raise last_error

@RetryPipeline.stage(attempts=3, backoff=2)
class FetchStage(RetryableStage):
    def process(self, source_id):
        return fetch_from_source(source_id)

@RetryPipeline.stage(attempts=2, backoff=1)
class TransformStage(RetryableStage):
    def process(self, data):
        return transform_data(data)

@RetryPipeline.stage(attempts=5, backoff=2)
class PushStage(RetryableStage):
    def process(self, data):
        push_to_destination(data)
        return data

RetryPipeline.run(source_id)
```

---

## 2.10 Composable Pipeline
**Scenario:** E-commerce checkout — combine user pipeline and order pipeline

**Imperative**
```python
def checkout(raw_user_data, raw_order_data):
    # user pipeline steps
    raw_user_data["email"] = raw_user_data["email"].lower().strip()
    raw_user_data["name"]  = raw_user_data["name"].strip().title()
    if not raw_user_data["email"] or "@" not in raw_user_data["email"]:
        raise ValidationError("invalid email")
    user = db.find_or_create_user(raw_user_data)

    # order pipeline steps
    raw_order_data["amount"] = round(raw_order_data["amount"], 2)
    raw_order_data["tax"]    = round(raw_order_data["amount"] * 0.1, 2)
    raw_order_data["total"]  = raw_order_data["amount"] + raw_order_data["tax"]
    if raw_order_data["total"] <= 0:
        raise ValidationError("invalid total")
    raw_order_data["user_id"] = user.id

    # combined final steps
    order   = db.create_order(raw_order_data)
    receipt = send_receipt(user, order)
    return {"user": user, "order": order, "receipt": receipt}
```

**Declarative**
```python
class Pipeline:
    def __init__(self, *stages):
        self._stages = list(stages)

    def run(self, data):
        return reduce(lambda d, fn: fn(d), self._stages, data)

    def then(self, other_pipeline):
        return Pipeline(*self._stages, *other_pipeline._stages)

# independent pipelines defined separately
user_pipeline = Pipeline(
    lambda d: {**d, "email": d["email"].lower().strip()},
    lambda d: {**d, "name":  d["name"].strip().title()},
    lambda d: (_ for _ in ()).throw(ValidationError("invalid email"))
              if not d["email"] or "@" not in d["email"] else d,
    lambda d: {**d, "user":  db.find_or_create_user(d)},
)

order_pipeline = Pipeline(
    lambda d: {**d, "amount": round(d["amount"], 2)},
    lambda d: {**d, "tax":    round(d["amount"] * 0.1, 2)},
    lambda d: {**d, "total":  d["amount"] + d["tax"]},
    lambda d: (_ for _ in ()).throw(ValidationError("invalid total"))
              if d["total"] <= 0 else d,
    lambda d: {**d, "user_id": d["user"].id},
    lambda d: {**d, "order":   db.create_order(d)},
)

receipt_pipeline = Pipeline(
    lambda d: {**d, "receipt": send_receipt(d["user"], d["order"])},
)

# compose all three into one
checkout_pipeline = user_pipeline.then(order_pipeline).then(receipt_pipeline)

result = checkout_pipeline.run({**raw_user_data, **raw_order_data})
```
# Chapter 3 — Reduce Patterns (Full Depth)
> Every pattern: real-world scenario, imperative code, declarative code

---

## 3.1 Basic Accumulation
**Scenario:** Invoice totaller — sum line items with quantity and unit price

**Imperative**
```python
def calculate_invoice_total(line_items):
    subtotal    = 0
    tax_total   = 0
    grand_total = 0

    for item in line_items:
        line_subtotal  = item.quantity * item.unit_price
        line_tax       = line_subtotal * item.tax_rate
        subtotal      += line_subtotal
        tax_total     += line_tax
        grand_total   += line_subtotal + line_tax

    return {
        "subtotal":    round(subtotal, 2),
        "tax":         round(tax_total, 2),
        "grand_total": round(grand_total, 2),
    }
```

**Declarative**
```python
def calculate_invoice_total(line_items):
    def accumulate(acc, item):
        subtotal = item.quantity * item.unit_price
        tax      = subtotal * item.tax_rate
        return {
            "subtotal":    acc["subtotal"]    + subtotal,
            "tax":         acc["tax"]         + tax,
            "grand_total": acc["grand_total"] + subtotal + tax,
        }

    raw = reduce(accumulate, line_items, {
        "subtotal": 0, "tax": 0, "grand_total": 0
    })

    return {k: round(v, 2) for k, v in raw.items()}
```

---

## 3.2 Building a Dictionary
**Scenario:** Build a lookup map of products by SKU from a flat list

**Imperative**
```python
def build_product_catalog(products):
    catalog = {}
    for product in products:
        if product.sku in catalog:
            # keep the one with higher stock
            if product.stock > catalog[product.sku].stock:
                catalog[product.sku] = product
        else:
            catalog[product.sku] = product
    return catalog
```

**Declarative**
```python
def build_product_catalog(products):
    def merge(catalog, product):
        existing = catalog.get(product.sku)
        winner   = product if not existing or product.stock > existing.stock else existing
        return {**catalog, product.sku: winner}

    return reduce(merge, products, {})
```

---

## 3.3 Flattening Structures
**Scenario:** Flatten a tree of category → subcategory → products into a flat product list

**Imperative**
```python
def flatten_catalog(categories):
    all_products = []
    for category in categories:
        for subcategory in category.subcategories:
            for product in subcategory.products:
                all_products.append({
                    **product.__dict__,
                    "category":    category.name,
                    "subcategory": subcategory.name,
                })
    return all_products
```

**Declarative**
```python
def flatten_catalog(categories):
    def expand_category(acc, category):
        def expand_sub(sub_acc, subcategory):
            def expand_product(prod_acc, product):
                return prod_acc + [{
                    **product.__dict__,
                    "category":    category.name,
                    "subcategory": subcategory.name,
                }]
            return reduce(expand_product, subcategory.products, sub_acc)
        return reduce(expand_sub, category.subcategories, acc)

    return reduce(expand_category, categories, [])
```

---

## 3.4 Running Statistics
**Scenario:** Real-time metrics aggregator for API response times

**Imperative**
```python
def aggregate_metrics(response_times):
    total   = 0
    count   = 0
    minimum = None
    maximum = None
    p95_buf = []

    for rt in response_times:
        total += rt
        count += 1
        if minimum is None or rt < minimum: minimum = rt
        if maximum is None or rt > maximum: maximum = rt
        p95_buf.append(rt)

    p95_buf.sort()
    p95_index = int(len(p95_buf) * 0.95)
    p95       = p95_buf[p95_index] if p95_buf else 0
    average   = total / count if count else 0

    return {
        "count":   count,
        "average": round(average, 2),
        "min":     minimum,
        "max":     maximum,
        "p95":     p95,
    }
```

**Declarative**
```python
def aggregate_metrics(response_times):
    def accumulate(acc, rt):
        return {
            "total":  acc["total"]  + rt,
            "count":  acc["count"]  + 1,
            "min":    min(acc["min"], rt) if acc["min"] is not None else rt,
            "max":    max(acc["max"], rt) if acc["max"] is not None else rt,
            "buffer": acc["buffer"] + [rt],
        }

    state = reduce(accumulate, response_times, {
        "total": 0, "count": 0, "min": None, "max": None, "buffer": []
    })

    sorted_buf = sorted(state["buffer"])
    p95_idx    = int(len(sorted_buf) * 0.95)

    return {
        "count":   state["count"],
        "average": round(state["total"] / state["count"], 2) if state["count"] else 0,
        "min":     state["min"],
        "max":     state["max"],
        "p95":     sorted_buf[p95_idx] if sorted_buf else 0,
    }
```

---

## 3.5 Reducer Registry
**Scenario:** Sales report — multiple independent aggregations over the same dataset

**Imperative**
```python
def generate_sales_report(transactions):
    total_revenue   = 0
    total_count     = 0
    refund_amount   = 0
    by_product      = {}
    by_region       = {}
    top_customer    = None
    top_amount      = 0

    for tx in transactions:
        total_revenue += tx.amount
        total_count   += 1

        if tx.type == "refund":
            refund_amount += tx.amount

        if tx.product_id not in by_product:
            by_product[tx.product_id] = 0
        by_product[tx.product_id] += tx.amount

        if tx.region not in by_region:
            by_region[tx.region] = 0
        by_region[tx.region] += tx.amount

        if tx.amount > top_amount:
            top_amount   = tx.amount
            top_customer = tx.customer_id

    return {
        "total_revenue": total_revenue,
        "total_count":   total_count,
        "refund_amount": refund_amount,
        "by_product":    by_product,
        "by_region":     by_region,
        "top_customer":  top_customer,
    }
```

**Declarative**
```python
class SalesReducerRegistry:
    _reducers = {}

    @classmethod
    def register(cls, name):
        def decorator(reducer_class):
            cls._reducers[name] = reducer_class()
            return reducer_class
        return decorator

    @classmethod
    def run(cls, transactions):
        return reduce(
            lambda acc, tx: {
                name: r.step(acc[name], tx)
                for name, r in cls._reducers.items()
            },
            transactions,
            {name: r.initial() for name, r in cls._reducers.items()}
        )

@SalesReducerRegistry.register("total_revenue")
class TotalRevenueReducer:
    def initial(self): return 0
    def step(self, acc, tx): return acc + tx.amount

@SalesReducerRegistry.register("total_count")
class TotalCountReducer:
    def initial(self): return 0
    def step(self, acc, tx): return acc + 1

@SalesReducerRegistry.register("refund_amount")
class RefundReducer:
    def initial(self): return 0
    def step(self, acc, tx):
        return acc + tx.amount if tx.type == "refund" else acc

@SalesReducerRegistry.register("by_product")
class ByProductReducer:
    def initial(self): return {}
    def step(self, acc, tx):
        return {**acc, tx.product_id: acc.get(tx.product_id, 0) + tx.amount}

@SalesReducerRegistry.register("by_region")
class ByRegionReducer:
    def initial(self): return {}
    def step(self, acc, tx):
        return {**acc, tx.region: acc.get(tx.region, 0) + tx.amount}

@SalesReducerRegistry.register("top_customer")
class TopCustomerReducer:
    def initial(self): return {"id": None, "amount": 0}
    def step(self, acc, tx):
        return {"id": tx.customer_id, "amount": tx.amount} if tx.amount > acc["amount"] else acc

SalesReducerRegistry.run(transactions)
```

---

## 3.6 Fold Left / Right
**Scenario:** Apply a chain of middleware transforms in defined order

**Imperative**
```python
def apply_transforms_left(data, transforms):
    result = data
    for transform in transforms:           # left → right
        result = transform(result)
    return result

def apply_transforms_right(data, transforms):
    result = data
    for transform in reversed(transforms): # right → left
        result = transform(result)
    return result
```

**Declarative**
```python
class FoldRegistry:
    _transforms = []

    @classmethod
    def transform(cls, fn):
        cls._transforms.append(fn)
        return fn

    @classmethod
    def fold_left(cls, data):
        return reduce(lambda d, fn: fn(d), cls._transforms, data)

    @classmethod
    def fold_right(cls, data):
        return reduce(lambda d, fn: fn(d), reversed(cls._transforms), data)

@FoldRegistry.transform
def sanitize(data): return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

@FoldRegistry.transform
def normalize_keys(data): return {k.lower(): v for k, v in data.items()}

@FoldRegistry.transform
def remove_nulls(data): return {k: v for k, v in data.items() if v is not None}

FoldRegistry.fold_left(raw_data)   # sanitize → normalize → remove_nulls
FoldRegistry.fold_right(raw_data)  # remove_nulls → normalize → sanitize
```

---

## 3.7 Scan (Running Reduce)
**Scenario:** Portfolio tracker — show running balance after each transaction

**Imperative**
```python
def running_balance(transactions):
    balance  = 0
    history  = []

    for tx in transactions:
        if tx.type == "credit":
            balance += tx.amount
        elif tx.type == "debit":
            balance -= tx.amount
        history.append({
            "tx_id":   tx.id,
            "date":    tx.date,
            "amount":  tx.amount,
            "type":    tx.type,
            "balance": round(balance, 2),
        })

    return history
```

**Declarative**
```python
def running_balance(transactions):
    def scan_step(acc, tx):
        delta      = tx.amount if tx.type == "credit" else -tx.amount
        new_balance = acc[-1]["balance"] + delta
        return acc + [{
            "tx_id":   tx.id,
            "date":    tx.date,
            "amount":  tx.amount,
            "type":    tx.type,
            "balance": round(new_balance, 2),
        }]

    return reduce(scan_step, transactions, [{"balance": 0}])[1:]
```

---

## 3.8 Tree Reduction
**Scenario:** File system — compute total size of a directory tree

**Imperative**
```python
def total_size(node):
    if node.type == "file":
        return node.size

    total = 0
    for child in node.children:
        if child.type == "file":
            total += child.size
        elif child.type == "directory":
            total += total_size(child)
    return total
```

**Declarative**
```python
class TreeSizeReducer:
    _handlers = {}

    @classmethod
    def handles(cls, node_type):
        def decorator(fn):
            cls._handlers[node_type] = fn
            return fn
        return decorator

    @classmethod
    def reduce(cls, node):
        handler = cls._handlers.get(node.type, cls._handlers["default"])
        return handler(node)

@TreeSizeReducer.handles("file")
def _(node): return node.size

@TreeSizeReducer.handles("directory")
def _(node):
    return reduce(
        lambda acc, child: acc + TreeSizeReducer.reduce(child),
        node.children,
        0
    )

@TreeSizeReducer.handles("default")
def _(node): return 0

TreeSizeReducer.reduce(root_directory)
```

---

## 3.9 Async Reduce
**Scenario:** Fetch prices from multiple providers and find the cheapest

**Imperative**
```python
async def find_cheapest_price(product_id, providers):
    cheapest_price    = None
    cheapest_provider = None

    for provider in providers:
        price = await fetch_price(provider, product_id)
        if cheapest_price is None or price < cheapest_price:
            cheapest_price    = price
            cheapest_provider = provider

    return {"provider": cheapest_provider, "price": cheapest_price}
```

**Declarative**
```python
async def find_cheapest_price(product_id, providers):
    prices = await asyncio.gather(*[
        fetch_price(provider, product_id) for provider in providers
    ])

    provider_prices = list(zip(providers, prices))

    return reduce(
        lambda cheapest, pair: pair if pair[1] < cheapest[1] else cheapest,
        provider_prices,
        (None, float("inf"))
    )
```

---

## 3.10 Transducer Pattern
**Scenario:** Process a massive event stream — filter, transform, limit without multiple passes

**Imperative**
```python
def process_events(events, max_results=100):
    results = []
    for event in events:
        if event.type != "purchase":      # filter
            continue
        if event.amount < 100:            # filter
            continue
        transformed = {                   # transform
            "user_id":   event.user_id,
            "amount":    round(event.amount, 2),
            "timestamp": event.timestamp.isoformat(),
        }
        results.append(transformed)
        if len(results) >= max_results:   # limit
            break
    return results
```

**Declarative**
```python
def filtering(predicate):
    def transducer(reducer):
        def step(acc, item):
            return reducer(acc, item) if predicate(item) else acc
        return step
    return transducer

def mapping(transform_fn):
    def transducer(reducer):
        def step(acc, item):
            return reducer(acc, transform_fn(item))
        return step
    return transducer

def taking(n):
    def transducer(reducer):
        count = [0]
        def step(acc, item):
            if count[0] >= n:
                return acc
            count[0] += 1
            return reducer(acc, item)
        return step
    return transducer

def compose(*transducers):
    def composed(reducer):
        return reduce(lambda r, t: t(r), reversed(transducers), reducer)
    return composed

def transduce(xform, items):
    reducer  = lambda acc, x: acc + [x]
    composed = xform(reducer)
    return reduce(composed, items, [])

xform = compose(
    filtering(lambda e: e.type == "purchase"),
    filtering(lambda e: e.amount >= 100),
    mapping(lambda e: {
        "user_id":   e.user_id,
        "amount":    round(e.amount, 2),
        "timestamp": e.timestamp.isoformat(),
    }),
    taking(100),
)

transduce(xform, events)
```
# Chapters 4–8 — Full Depth
> Filter, Rules as Data, Recursion, Concurrency, State Machines

---

# CHAPTER 4 — Filter Patterns

---

## 4.1 Basic Filter
**Scenario:** Product search — return only in-stock products

**Imperative**
```python
def get_available_products(products):
    available = []
    for product in products:
        if product.in_stock and product.active and not product.discontinued:
            available.append(product)
    return available
```

**Declarative**
```python
class ProductFilter:
    _predicates = []

    @classmethod
    def predicate(cls, fn):
        cls._predicates.append(fn)
        return fn

    @classmethod
    def apply(cls, products):
        return reduce(
            lambda items, pred: filter(pred, items),
            cls._predicates,
            products
        )

@ProductFilter.predicate
def _(p): return p.in_stock

@ProductFilter.predicate
def _(p): return p.active

@ProductFilter.predicate
def _(p): return not p.discontinued

list(ProductFilter.apply(products))
```

---

## 4.2 Composable Filter Registry
**Scenario:** User search with named, composable filters

**Imperative**
```python
def search_users(users, filters):
    results = []
    for user in users:
        if "active" in filters and not user.active:
            continue
        if "verified" in filters and not user.email_verified:
            continue
        if "premium" in filters and user.plan != "premium":
            continue
        if "recent" in filters:
            cutoff = datetime.now() - timedelta(days=30)
            if user.last_login < cutoff:
                continue
        results.append(user)
    return results
```

**Declarative**
```python
class UserFilterRegistry:
    _filters = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._filters[name] = fn
            return fn
        return decorator

    @classmethod
    def apply(cls, users, *filter_names):
        return reduce(
            lambda data, name: filter(cls._filters[name], data),
            filter_names,
            users
        )

@UserFilterRegistry.register("active")
def _(u): return u.active

@UserFilterRegistry.register("verified")
def _(u): return u.email_verified

@UserFilterRegistry.register("premium")
def _(u): return u.plan == "premium"

@UserFilterRegistry.register("recent")
def _(u): return u.last_login >= datetime.now() - timedelta(days=30)

list(UserFilterRegistry.apply(users, "active", "verified", "premium"))
```

---

## 4.3 Filter with Scoring
**Scenario:** Job matching — candidates must score above threshold

**Imperative**
```python
def match_candidates(candidates, job, min_score):
    results = []
    for candidate in candidates:
        score = 0
        if candidate.years_experience >= job.required_experience:
            score += 40
        if job.required_skill in candidate.skills:
            score += 30
        if candidate.location == job.location:
            score += 20
        if candidate.salary_expectation <= job.salary_max:
            score += 10
        if score >= min_score:
            results.append({"candidate": candidate, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
```

**Declarative**
```python
class CandidateScoringFilter:
    _rules = []

    @classmethod
    def rule(cls, points):
        def decorator(fn):
            cls._rules.append((fn, points))
            return fn
        return decorator

    @classmethod
    def match(cls, candidates, job, min_score):
        def score(candidate):
            return sum(pts for check, pts in cls._rules if check(candidate, job))

        scored  = ((c, score(c)) for c in candidates)
        passing = ((c, s) for c, s in scored if s >= min_score)
        return sorted(passing, key=lambda x: x[1], reverse=True)

@CandidateScoringFilter.rule(points=40)
def _(c, job): return c.years_experience >= job.required_experience

@CandidateScoringFilter.rule(points=30)
def _(c, job): return job.required_skill in c.skills

@CandidateScoringFilter.rule(points=20)
def _(c, job): return c.location == job.location

@CandidateScoringFilter.rule(points=10)
def _(c, job): return c.salary_expectation <= job.salary_max

CandidateScoringFilter.match(candidates, job, min_score=50)
```

---

## 4.4 Lazy Filter Chain
**Scenario:** Process millions of sensor readings — memory-constrained environment

**Imperative**
```python
def process_sensor_data(file_path):
    with open(file_path) as f:
        lines = f.readlines()              # entire file in memory

    valid   = []
    for line in lines:
        reading = parse_reading(line)
        if reading and reading.sensor_id:
            valid.append(reading)

    recent  = []
    cutoff  = datetime.now() - timedelta(hours=24)
    for r in valid:
        if r.timestamp >= cutoff:
            recent.append(r)

    anomalies = []
    for r in recent:
        if r.value > THRESHOLD or r.value < LOWER_THRESHOLD:
            anomalies.append(r)

    return anomalies
```

**Declarative**
```python
class SensorFilterChain:
    _stages = []

    @classmethod
    def stage(cls, fn):
        cls._stages.append(fn)
        return fn

    @classmethod
    def process(cls, source):
        return reduce(lambda stream, fn: fn(stream), cls._stages, source)

def read_sensor_file(file_path):
    with open(file_path) as f:
        for line in f:
            yield line           # one line at a time — constant memory

@SensorFilterChain.stage
def parse(lines):
    return (parse_reading(line) for line in lines)

@SensorFilterChain.stage
def filter_valid(readings):
    return (r for r in readings if r and r.sensor_id)

@SensorFilterChain.stage
def filter_recent(readings):
    cutoff = datetime.now() - timedelta(hours=24)
    return (r for r in readings if r.timestamp >= cutoff)

@SensorFilterChain.stage
def filter_anomalies(readings):
    return (r for r in readings if r.value > THRESHOLD or r.value < LOWER_THRESHOLD)

list(SensorFilterChain.process(read_sensor_file(file_path)))
```

---

## 4.5 Partition Filter
**Scenario:** Email validator — split list into valid and invalid

**Imperative**
```python
def partition_emails(email_list):
    valid   = []
    invalid = []
    for email in email_list:
        if "@" in email and "." in email.split("@")[-1] and len(email) >= 5:
            valid.append(email)
        else:
            invalid.append(email)
    return valid, invalid
```

**Declarative**
```python
class EmailPartitioner:
    _rules = []

    @classmethod
    def rule(cls, fn):
        cls._rules.append(fn)
        return fn

    @classmethod
    def partition(cls, emails):
        def is_valid(email):
            return all(rule(email) for rule in cls._rules)

        valid   = (e for e in emails if is_valid(e))
        invalid = (e for e in emails if not is_valid(e))
        return valid, invalid

@EmailPartitioner.rule
def _(e): return "@" in e

@EmailPartitioner.rule
def _(e): return "." in e.split("@")[-1]

@EmailPartitioner.rule
def _(e): return len(e) >= 5

valid_emails, invalid_emails = EmailPartitioner.partition(email_list)
```

---

## 4.6 Async Filter
**Scenario:** Filter products by real-time inventory availability

**Imperative**
```python
async def filter_in_stock(products):
    available = []
    for product in products:
        stock = await inventory_service.check(product.id)
        if stock > 0:
            available.append(product)
    return available
```

**Declarative**
```python
class AsyncInventoryFilter:
    _checks = []

    @classmethod
    def check(cls, fn):
        cls._checks.append(fn)
        return fn

    @classmethod
    async def apply(cls, products):
        async def passes_all(product):
            results = await asyncio.gather(*[check(product) for check in cls._checks])
            return all(results)

        checks  = await asyncio.gather(*[passes_all(p) for p in products])
        return [p for p, passed in zip(products, checks) if passed]

@AsyncInventoryFilter.check
async def _(product): return await inventory_service.check(product.id) > 0

@AsyncInventoryFilter.check
async def _(product): return await pricing_service.has_price(product.id)

await AsyncInventoryFilter.apply(products)
```

---

# CHAPTER 5 — Rules as Data Patterns

---

## 5.1 Scoring Engine
**Scenario:** Credit risk scoring system

**Imperative**
```python
def score_credit_application(application):
    score = 500  # base score

    if application.income >= 100000:
        score += 100
    elif application.income >= 60000:
        score += 60
    elif application.income >= 30000:
        score += 30

    if application.credit_history_years >= 10:
        score += 80
    elif application.credit_history_years >= 5:
        score += 50
    elif application.credit_history_years >= 2:
        score += 20

    if application.debt_to_income < 0.2:
        score += 70
    elif application.debt_to_income < 0.4:
        score += 40
    elif application.debt_to_income > 0.6:
        score -= 50

    if application.missed_payments == 0:
        score += 100
    elif application.missed_payments <= 2:
        score -= 50
    else:
        score -= 150

    return max(300, min(850, score))
```

**Declarative**
```python
class CreditScoringEngine:
    _rules = []
    _base  = 500

    @classmethod
    def rule(cls, points):
        def decorator(fn):
            cls._rules.append((fn, points))
            return fn
        return decorator

    @classmethod
    def score(cls, application):
        total = cls._base + sum(
            pts for check, pts in cls._rules if check(application)
        )
        return max(300, min(850, total))

@CreditScoringEngine.rule(points=100)
def _(a): return a.income >= 100000

@CreditScoringEngine.rule(points=60)
def _(a): return 60000 <= a.income < 100000

@CreditScoringEngine.rule(points=30)
def _(a): return 30000 <= a.income < 60000

@CreditScoringEngine.rule(points=80)
def _(a): return a.credit_history_years >= 10

@CreditScoringEngine.rule(points=50)
def _(a): return 5 <= a.credit_history_years < 10

@CreditScoringEngine.rule(points=20)
def _(a): return 2 <= a.credit_history_years < 5

@CreditScoringEngine.rule(points=70)
def _(a): return a.debt_to_income < 0.2

@CreditScoringEngine.rule(points=40)
def _(a): return 0.2 <= a.debt_to_income < 0.4

@CreditScoringEngine.rule(points=-50)
def _(a): return a.debt_to_income > 0.6

@CreditScoringEngine.rule(points=100)
def _(a): return a.missed_payments == 0

@CreditScoringEngine.rule(points=-50)
def _(a): return 1 <= a.missed_payments <= 2

@CreditScoringEngine.rule(points=-150)
def _(a): return a.missed_payments > 2

CreditScoringEngine.score(application)
```

---

## 5.2 Validation Engine
**Scenario:** Multi-field form validator with detailed error messages

**Imperative**
```python
def validate_signup_form(form):
    errors = {}

    if not form.get("username"):
        errors["username"] = "username is required"
    elif len(form["username"]) < 3:
        errors["username"] = "username must be at least 3 characters"
    elif not re.match(r"^[a-zA-Z0-9_]+$", form["username"]):
        errors["username"] = "username can only contain letters, numbers, underscores"

    if not form.get("email"):
        errors["email"] = "email is required"
    elif "@" not in form["email"]:
        errors["email"] = "email must contain @"
    elif "." not in form["email"].split("@")[-1]:
        errors["email"] = "email domain is invalid"

    if not form.get("password"):
        errors["password"] = "password is required"
    elif len(form["password"]) < 8:
        errors["password"] = "password must be at least 8 characters"
    elif not re.search(r"[A-Z]", form["password"]):
        errors["password"] = "password must contain an uppercase letter"
    elif not re.search(r"[0-9]", form["password"]):
        errors["password"] = "password must contain a number"

    return errors
```

**Declarative**
```python
class FormValidationEngine:
    _field_rules = {}

    @classmethod
    def field(cls, field_name):
        def decorator(rule_class):
            cls._field_rules.setdefault(field_name, []).append(rule_class())
            return rule_class
        return decorator

    @classmethod
    def validate(cls, form):
        errors = {}
        for field, rules in cls._field_rules.items():
            for rule in rules:
                error = rule.check(form.get(field), form)
                if error:
                    errors[field] = error
                    break
        return errors

@FormValidationEngine.field("username")
class UsernameRequired:
    def check(self, value, form):
        return "username is required" if not value else None

@FormValidationEngine.field("username")
class UsernameLength:
    def check(self, value, form):
        return "username must be at least 3 characters" if value and len(value) < 3 else None

@FormValidationEngine.field("username")
class UsernameFormat:
    def check(self, value, form):
        if value and not re.match(r"^[a-zA-Z0-9_]+$", value):
            return "username can only contain letters, numbers, underscores"
        return None

@FormValidationEngine.field("email")
class EmailRequired:
    def check(self, value, form):
        return "email is required" if not value else None

@FormValidationEngine.field("email")
class EmailFormat:
    def check(self, value, form):
        return "email must contain @" if value and "@" not in value else None

@FormValidationEngine.field("password")
class PasswordRequired:
    def check(self, value, form):
        return "password is required" if not value else None

@FormValidationEngine.field("password")
class PasswordLength:
    def check(self, value, form):
        return "password must be at least 8 characters" if value and len(value) < 8 else None

@FormValidationEngine.field("password")
class PasswordUppercase:
    def check(self, value, form):
        return "password must contain an uppercase letter" if value and not re.search(r"[A-Z]", value) else None

@FormValidationEngine.field("password")
class PasswordNumber:
    def check(self, value, form):
        return "password must contain a number" if value and not re.search(r"[0-9]", value) else None

FormValidationEngine.validate(form)
```

---

## 5.3 Pricing Engine
**Scenario:** SaaS subscription pricing with discounts and add-ons

**Imperative**
```python
def calculate_subscription_price(plan, user, addons):
    base = {"starter": 29, "pro": 79, "enterprise": 199}.get(plan, 29)

    # annual discount
    if user.billing_cycle == "annual":
        base = base * 12 * 0.8   # 20% off annual

    # team size discount
    if user.team_size >= 50:
        base *= 0.85
    elif user.team_size >= 20:
        base *= 0.90

    # nonprofit discount
    if user.is_nonprofit:
        base *= 0.70

    # add-ons
    addon_total = 0
    for addon in addons:
        if addon == "advanced_analytics":
            addon_total += 49
        elif addon == "priority_support":
            addon_total += 99
        elif addon == "custom_domain":
            addon_total += 19
        elif addon == "sso":
            addon_total += 149

    return round(base + addon_total, 2)
```

**Declarative**
```python
class SubscriptionPricingEngine:
    _base_prices  = {}
    _modifiers    = []
    _addon_prices = {}

    @classmethod
    def base_plan(cls, plan, price):
        cls._base_prices[plan] = price
        return price

    @classmethod
    def modifier(cls, priority=0):
        def decorator(mod_class):
            cls._modifiers.append((priority, mod_class()))
            cls._modifiers.sort(key=lambda x: x[0], reverse=True)
            return mod_class
        return decorator

    @classmethod
    def addon(cls, name, price):
        cls._addon_prices[name] = price
        return price

    @classmethod
    def calculate(cls, plan, user, addons):
        base = cls._base_prices.get(plan, 29)

        discounted = reduce(
            lambda price, item: item[1].apply(price, user),
            cls._modifiers,
            base
        )

        addon_total = sum(cls._addon_prices.get(a, 0) for a in addons)
        return round(discounted + addon_total, 2)

SubscriptionPricingEngine.base_plan("starter",    29)
SubscriptionPricingEngine.base_plan("pro",        79)
SubscriptionPricingEngine.base_plan("enterprise", 199)

SubscriptionPricingEngine.addon("advanced_analytics", 49)
SubscriptionPricingEngine.addon("priority_support",   99)
SubscriptionPricingEngine.addon("custom_domain",      19)
SubscriptionPricingEngine.addon("sso",               149)

@SubscriptionPricingEngine.modifier(priority=100)
class AnnualBillingModifier:
    def apply(self, price, user):
        return price * 12 * 0.8 if user.billing_cycle == "annual" else price

@SubscriptionPricingEngine.modifier(priority=50)
class TeamSizeModifier:
    def apply(self, price, user):
        if user.team_size >= 50:  return price * 0.85
        if user.team_size >= 20:  return price * 0.90
        return price

@SubscriptionPricingEngine.modifier(priority=10)
class NonprofitModifier:
    def apply(self, price, user):
        return price * 0.70 if user.is_nonprofit else price

SubscriptionPricingEngine.calculate("pro", user, ["sso", "advanced_analytics"])
```

---

# CHAPTER 6 — Recursion Patterns

---

## 6.1 Type-dispatch Recursion
**Scenario:** Render a UI component tree to HTML string

**Imperative**
```python
def render(node):
    if node["type"] == "page":
        children = "".join(render(c) for c in node["children"])
        return f"<html><body>{children}</body></html>"
    elif node["type"] == "section":
        children = "".join(render(c) for c in node["children"])
        return f'<section class="{node.get("class", "")}">{children}</section>'
    elif node["type"] == "heading":
        level = node.get("level", 1)
        return f'<h{level}>{node["text"]}</h{level}>'
    elif node["type"] == "paragraph":
        return f'<p>{node["text"]}</p>'
    elif node["type"] == "image":
        return f'<img src="{node["src"]}" alt="{node.get("alt", "")}" />'
    elif node["type"] == "link":
        return f'<a href="{node["href"]}">{node["text"]}</a>'
    else:
        return ""
```

**Declarative**
```python
class RenderRegistry:
    _renderers = {}

    @classmethod
    def handles(cls, node_type):
        def decorator(fn):
            cls._renderers[node_type] = fn
            return fn
        return decorator

    @classmethod
    def render(cls, node):
        renderer = cls._renderers.get(node["type"], cls._renderers["default"])
        return renderer(node)

def render_children(node):
    return "".join(RenderRegistry.render(c) for c in node.get("children", []))

@RenderRegistry.handles("page")
def _(node):
    return f"<html><body>{render_children(node)}</body></html>"

@RenderRegistry.handles("section")
def _(node):
    return f'<section class="{node.get("class", "")}">{render_children(node)}</section>'

@RenderRegistry.handles("heading")
def _(node):
    level = node.get("level", 1)
    return f'<h{level}>{node["text"]}</h{level}>'

@RenderRegistry.handles("paragraph")
def _(node):
    return f'<p>{node["text"]}</p>'

@RenderRegistry.handles("image")
def _(node):
    return f'<img src="{node["src"]}" alt="{node.get("alt", "")}" />'

@RenderRegistry.handles("link")
def _(node):
    return f'<a href="{node["href"]}">{node["text"]}</a>'

@RenderRegistry.handles("default")
def _(node): return ""

RenderRegistry.render(component_tree)
```

---

## 6.2 Tree Traversal Registry
**Scenario:** Find all nodes in an org chart that match a predicate

**Imperative**
```python
def find_employees(org_node, predicate):
    results = []
    if predicate(org_node):
        results.append(org_node)
    for report in org_node.direct_reports:
        results.extend(find_employees(report, predicate))
    return results

# Find all senior engineers in department
senior_engineers = find_employees(
    cto_node,
    lambda e: e.title == "Senior Engineer" and e.department == "Engineering"
)
```

**Declarative**
```python
class OrgChartTraversal:
    _strategies = {}

    @classmethod
    def strategy(cls, name):
        def decorator(fn):
            cls._strategies[name] = fn
            return fn
        return decorator

    @classmethod
    def find(cls, root, predicate, strategy="depth_first"):
        return cls._strategies[strategy](root, predicate)

@OrgChartTraversal.strategy("depth_first")
def _(root, predicate):
    stack   = [root]
    matches = []
    while stack:
        node = stack.pop()
        if predicate(node):
            matches.append(node)
        stack.extend(reversed(node.direct_reports))
    return matches

@OrgChartTraversal.strategy("breadth_first")
def _(root, predicate):
    queue   = deque([root])
    matches = []
    while queue:
        node = queue.popleft()
        if predicate(node):
            matches.append(node)
        queue.extend(node.direct_reports)
    return matches

@OrgChartTraversal.strategy("leaves_only")
def _(root, predicate):
    stack   = [root]
    matches = []
    while stack:
        node = stack.pop()
        if not node.direct_reports and predicate(node):
            matches.append(node)
        stack.extend(node.direct_reports)
    return matches

OrgChartTraversal.find(
    cto_node,
    lambda e: e.title == "Senior Engineer",
    strategy="breadth_first"
)
```

---

## 6.3 AST Evaluation Registry
**Scenario:** Formula evaluator for a spreadsheet engine

**Imperative**
```python
def evaluate_formula(node, context):
    if node["type"] == "number":
        return float(node["value"])
    elif node["type"] == "cell_ref":
        return context.get_cell(node["ref"])
    elif node["type"] == "binary_op":
        left  = evaluate_formula(node["left"], context)
        right = evaluate_formula(node["right"], context)
        if node["op"] == "+": return left + right
        elif node["op"] == "-": return left - right
        elif node["op"] == "*": return left * right
        elif node["op"] == "/": return left / right if right != 0 else "#DIV/0!"
    elif node["type"] == "function_call":
        args = [evaluate_formula(a, context) for a in node["args"]]
        if node["name"] == "SUM":   return sum(args)
        elif node["name"] == "AVG": return sum(args) / len(args) if args else 0
        elif node["name"] == "MAX": return max(args)
        elif node["name"] == "MIN": return min(args)
    elif node["type"] == "conditional":
        cond = evaluate_formula(node["condition"], context)
        return evaluate_formula(node["true_branch"] if cond else node["false_branch"], context)
```

**Declarative**
```python
class FormulaEvaluator:
    _evaluators = {}
    _functions  = {}

    @classmethod
    def handles(cls, node_type):
        def decorator(fn):
            cls._evaluators[node_type] = fn
            return fn
        return decorator

    @classmethod
    def function(cls, name):
        def decorator(fn):
            cls._functions[name] = fn
            return fn
        return decorator

    @classmethod
    def evaluate(cls, node, context):
        evaluator = cls._evaluators.get(node["type"], cls._evaluators["default"])
        return evaluator(node, context)

@FormulaEvaluator.handles("number")
def _(node, ctx): return float(node["value"])

@FormulaEvaluator.handles("cell_ref")
def _(node, ctx): return ctx.get_cell(node["ref"])

@FormulaEvaluator.handles("binary_op")
def _(node, ctx):
    ops = {
        "+": lambda l, r: l + r,
        "-": lambda l, r: l - r,
        "*": lambda l, r: l * r,
        "/": lambda l, r: l / r if r != 0 else "#DIV/0!",
    }
    left  = FormulaEvaluator.evaluate(node["left"], ctx)
    right = FormulaEvaluator.evaluate(node["right"], ctx)
    return ops.get(node["op"], lambda l, r: "#UNKNOWN_OP!")(left, right)

@FormulaEvaluator.handles("function_call")
def _(node, ctx):
    args = [FormulaEvaluator.evaluate(a, ctx) for a in node["args"]]
    fn   = FormulaEvaluator._functions.get(node["name"])
    return fn(args) if fn else f"#NAME_ERROR:{node['name']}"

@FormulaEvaluator.handles("conditional")
def _(node, ctx):
    condition = FormulaEvaluator.evaluate(node["condition"], ctx)
    branch    = node["true_branch"] if condition else node["false_branch"]
    return FormulaEvaluator.evaluate(branch, ctx)

@FormulaEvaluator.handles("default")
def _(node, ctx): return "#UNKNOWN_NODE!"

@FormulaEvaluator.function("SUM")
def _(args): return sum(args)

@FormulaEvaluator.function("AVG")
def _(args): return sum(args) / len(args) if args else 0

@FormulaEvaluator.function("MAX")
def _(args): return max(args)

@FormulaEvaluator.function("MIN")
def _(args): return min(args)

FormulaEvaluator.evaluate(ast_root, spreadsheet_context)
```

---

# CHAPTER 7 — Concurrency Patterns

---

## 7.1 Parallel Gather
**Scenario:** Microservice aggregator — combine data from 5 services in one response

**Imperative**
```python
async def get_product_detail(product_id, user_id):
    product         = await product_service.get(product_id)
    reviews         = await review_service.get_for_product(product_id)
    inventory       = await inventory_service.check(product_id)
    recommendations = await rec_service.get_similar(product_id, user_id)
    user_history    = await history_service.get_interactions(user_id, product_id)

    return {
        "product":         product,
        "reviews":         reviews,
        "inventory":       inventory,
        "recommendations": recommendations,
        "user_history":    user_history,
    }
```

**Declarative**
```python
class ProductDetailAggregator:
    _sources = {}

    @classmethod
    def source(cls, name):
        def decorator(fn):
            cls._sources[name] = fn
            return fn
        return decorator

    @classmethod
    async def aggregate(cls, context):
        results = await asyncio.gather(
            *[fn(context) for fn in cls._sources.values()],
            return_exceptions=True
        )
        return {
            name: result if not isinstance(result, Exception) else None
            for name, result in zip(cls._sources.keys(), results)
        }

@ProductDetailAggregator.source("product")
async def _(ctx): return await product_service.get(ctx.product_id)

@ProductDetailAggregator.source("reviews")
async def _(ctx): return await review_service.get_for_product(ctx.product_id)

@ProductDetailAggregator.source("inventory")
async def _(ctx): return await inventory_service.check(ctx.product_id)

@ProductDetailAggregator.source("recommendations")
async def _(ctx): return await rec_service.get_similar(ctx.product_id, ctx.user_id)

@ProductDetailAggregator.source("user_history")
async def _(ctx): return await history_service.get_interactions(ctx.user_id, ctx.product_id)

await ProductDetailAggregator.aggregate(context)
```

---

## 7.2 Failure-isolated Gather
**Scenario:** Batch notification sender — one failure must not stop others

**Imperative**
```python
async def send_batch_notifications(notifications):
    results = []
    for notif in notifications:
        try:
            if notif.channel == "email":
                await email_service.send(notif.recipient, notif.content)
                results.append({"id": notif.id, "status": "sent"})
            elif notif.channel == "sms":
                await sms_service.send(notif.recipient, notif.content)
                results.append({"id": notif.id, "status": "sent"})
            elif notif.channel == "push":
                await push_service.send(notif.recipient, notif.content)
                results.append({"id": notif.id, "status": "sent"})
        except Exception as e:
            results.append({"id": notif.id, "status": "failed", "error": str(e)})
    return results
```

**Declarative**
```python
class NotificationDispatcher:
    _channels = {}

    @classmethod
    def channel(cls, name):
        def decorator(handler_class):
            cls._channels[name] = handler_class()
            return handler_class
        return decorator

    @classmethod
    async def dispatch(cls, notifications):
        async def send_one(notif):
            try:
                handler = cls._channels.get(notif.channel, cls._channels["default"])
                await handler.send(notif)
                return {"id": notif.id, "status": "sent"}
            except Exception as e:
                return {"id": notif.id, "status": "failed", "error": str(e)}

        return await asyncio.gather(*[send_one(n) for n in notifications])

@NotificationDispatcher.channel("email")
class EmailChannel:
    async def send(self, notif): await email_service.send(notif.recipient, notif.content)

@NotificationDispatcher.channel("sms")
class SmsChannel:
    async def send(self, notif): await sms_service.send(notif.recipient, notif.content)

@NotificationDispatcher.channel("push")
class PushChannel:
    async def send(self, notif): await push_service.send(notif.recipient, notif.content)

@NotificationDispatcher.channel("default")
class NullChannel:
    async def send(self, notif): raise ValueError(f"Unknown channel: {notif.channel}")

await NotificationDispatcher.dispatch(notifications)
```

---

# CHAPTER 8 — State Machine Patterns

---

## 8.1 Basic State Machine
**Scenario:** Subscription lifecycle — trial, active, paused, cancelled, expired

**Imperative**
```python
def transition_subscription(subscription, event):
    if subscription.state == "trial":
        if event == "upgrade":
            subscription.state = "active"
            subscription.billing_start = datetime.now()
        elif event == "expire":
            subscription.state = "expired"
        elif event == "cancel":
            subscription.state = "cancelled"

    elif subscription.state == "active":
        if event == "pause":
            subscription.state = "paused"
            subscription.paused_at = datetime.now()
        elif event == "cancel":
            subscription.state = "cancelled"
            subscription.cancelled_at = datetime.now()
        elif event == "expire":
            subscription.state = "expired"

    elif subscription.state == "paused":
        if event == "resume":
            subscription.state = "active"
            subscription.paused_at = None
        elif event == "cancel":
            subscription.state = "cancelled"
            subscription.cancelled_at = datetime.now()

    return subscription
```

**Declarative**
```python
class SubscriptionStateMachine:
    _transitions = {}

    @classmethod
    def transition(cls, from_state, event):
        def decorator(fn):
            cls._transitions[(from_state, event)] = fn
            return fn
        return decorator

    @classmethod
    def dispatch(cls, subscription, event):
        handler = cls._transitions.get((subscription.state, event), noop_transition)
        return handler(subscription)

def noop_transition(subscription):
    return subscription

@SubscriptionStateMachine.transition("trial", "upgrade")
def _(sub): return replace(sub, state="active", billing_start=datetime.now())

@SubscriptionStateMachine.transition("trial", "expire")
def _(sub): return replace(sub, state="expired")

@SubscriptionStateMachine.transition("trial", "cancel")
def _(sub): return replace(sub, state="cancelled")

@SubscriptionStateMachine.transition("active", "pause")
def _(sub): return replace(sub, state="paused", paused_at=datetime.now())

@SubscriptionStateMachine.transition("active", "cancel")
def _(sub): return replace(sub, state="cancelled", cancelled_at=datetime.now())

@SubscriptionStateMachine.transition("active", "expire")
def _(sub): return replace(sub, state="expired")

@SubscriptionStateMachine.transition("paused", "resume")
def _(sub): return replace(sub, state="active", paused_at=None)

@SubscriptionStateMachine.transition("paused", "cancel")
def _(sub): return replace(sub, state="cancelled", cancelled_at=datetime.now())

SubscriptionStateMachine.dispatch(subscription, "upgrade")
```

---

## 8.2 Guarded Transitions
**Scenario:** Bank account — prevent invalid transitions with pre-conditions

**Imperative**
```python
def process_transaction(account, event, amount=0):
    if account.state == "active":
        if event == "withdraw":
            if amount <= 0:
                raise ValueError("amount must be positive")
            if amount > account.balance:
                raise ValueError("insufficient funds")
            if account.daily_withdrawn + amount > account.daily_limit:
                raise ValueError("daily limit exceeded")
            account.balance          -= amount
            account.daily_withdrawn  += amount

        elif event == "freeze":
            if not account.is_admin_action:
                raise PermissionError("only admins can freeze")
            account.state = "frozen"

        elif event == "close":
            if account.balance > 0:
                raise ValueError("cannot close account with positive balance")
            account.state = "closed"

    elif account.state == "frozen":
        if event == "unfreeze":
            if not account.is_admin_action:
                raise PermissionError("only admins can unfreeze")
            account.state = "active"
```

**Declarative**
```python
class BankAccountStateMachine:
    _transitions = {}

    @classmethod
    def transition(cls, from_state, event):
        def decorator(transition_class):
            cls._transitions[(from_state, event)] = transition_class()
            return transition_class
        return decorator

    @classmethod
    def process(cls, account, event, **kwargs):
        key        = (account.state, event)
        transition = cls._transitions.get(key, NoopBankTransition())
        transition.guard(account, **kwargs)
        return transition.apply(account, **kwargs)

class NoopBankTransition:
    def guard(self, account, **kwargs): pass
    def apply(self, account, **kwargs): return account

@BankAccountStateMachine.transition("active", "withdraw")
class WithdrawTransition:
    def guard(self, account, amount=0, **kwargs):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > account.balance:
            raise ValueError("insufficient funds")
        if account.daily_withdrawn + amount > account.daily_limit:
            raise ValueError("daily limit exceeded")
    def apply(self, account, amount=0, **kwargs):
        return replace(account,
            balance=account.balance - amount,
            daily_withdrawn=account.daily_withdrawn + amount
        )

@BankAccountStateMachine.transition("active", "freeze")
class FreezeTransition:
    def guard(self, account, is_admin=False, **kwargs):
        if not is_admin: raise PermissionError("only admins can freeze")
    def apply(self, account, **kwargs):
        return replace(account, state="frozen")

@BankAccountStateMachine.transition("active", "close")
class CloseTransition:
    def guard(self, account, **kwargs):
        if account.balance > 0: raise ValueError("cannot close with positive balance")
    def apply(self, account, **kwargs):
        return replace(account, state="closed")

@BankAccountStateMachine.transition("frozen", "unfreeze")
class UnfreezeTransition:
    def guard(self, account, is_admin=False, **kwargs):
        if not is_admin: raise PermissionError("only admins can unfreeze")
    def apply(self, account, **kwargs):
        return replace(account, state="active")

BankAccountStateMachine.process(account, "withdraw", amount=500)
```

---

## 8.3 Action Registry
**Scenario:** Order workflow with side effects on each transition

**Imperative**
```python
def advance_order(order, event):
    if order.state == "pending" and event == "confirm":
        order.state      = "confirmed"
        order.confirmed_at = datetime.now()
        send_confirmation_email(order)
        reserve_inventory(order)
        notify_warehouse(order)

    elif order.state == "confirmed" and event == "ship":
        order.state    = "shipped"
        order.shipped_at = datetime.now()
        tracking       = create_shipment(order)
        order.tracking = tracking
        send_shipping_email(order)
        update_inventory_shipped(order)

    elif order.state == "shipped" and event == "deliver":
        order.state       = "delivered"
        order.delivered_at = datetime.now()
        send_delivery_confirmation(order)
        trigger_review_request(order)
        release_escrow(order)

    elif order.state == "confirmed" and event == "cancel":
        order.state      = "cancelled"
        order.cancelled_at = datetime.now()
        release_inventory(order)
        process_refund(order)
        send_cancellation_email(order)

    return order
```

**Declarative**
```python
class OrderWorkflow:
    _transitions = {}

    @classmethod
    def transition(cls, from_state, event, to_state):
        def decorator(actions_class):
            cls._transitions[(from_state, event)] = (to_state, actions_class())
            return actions_class
        return decorator

    @classmethod
    def advance(cls, order, event):
        key = (order.state, event)
        if key not in cls._transitions:
            return order
        to_state, actions = cls._transitions[key]
        updated = replace(order, state=to_state)
        actions.run(updated)
        return updated

@OrderWorkflow.transition("pending", "confirm", to_state="confirmed")
class ConfirmActions:
    def run(self, order):
        send_confirmation_email(order)
        reserve_inventory(order)
        notify_warehouse(order)

@OrderWorkflow.transition("confirmed", "ship", to_state="shipped")
class ShipActions:
    def run(self, order):
        tracking       = create_shipment(order)
        order.tracking = tracking
        send_shipping_email(order)
        update_inventory_shipped(order)

@OrderWorkflow.transition("shipped", "deliver", to_state="delivered")
class DeliverActions:
    def run(self, order):
        send_delivery_confirmation(order)
        trigger_review_request(order)
        release_escrow(order)

@OrderWorkflow.transition("confirmed", "cancel", to_state="cancelled")
class CancelActions:
    def run(self, order):
        release_inventory(order)
        process_refund(order)
        send_cancellation_email(order)

OrderWorkflow.advance(order, "confirm")
```
# Chapters 9–10 — Full Depth
> Complex Algorithms & Nested Structures

---

# CHAPTER 9 — Complex Algorithm Patterns

---

## 9.1 Sort Strategy Registry
**Scenario:** E-commerce search results with multiple sort modes

**Imperative**
```python
def sort_search_results(products, strategy, user_context):
    if strategy == "relevance":
        return sorted(products,
            key=lambda p: p.relevance_score,
            reverse=True
        )
    elif strategy == "price_low":
        return sorted(products, key=lambda p: p.price)
    elif strategy == "price_high":
        return sorted(products, key=lambda p: p.price, reverse=True)
    elif strategy == "rating":
        return sorted(products,
            key=lambda p: (p.avg_rating, p.review_count),
            reverse=True
        )
    elif strategy == "newest":
        return sorted(products, key=lambda p: p.created_at, reverse=True)
    elif strategy == "personalized":
        user_prefs = user_context.preferences
        return sorted(products,
            key=lambda p: sum(
                p.tags.count(pref) for pref in user_prefs
            ) + p.relevance_score,
            reverse=True
        )
    elif strategy == "trending":
        return sorted(products,
            key=lambda p: p.sales_last_7_days / max(p.days_listed, 1),
            reverse=True
        )
    else:
        return products
```

**Declarative**
```python
class SearchSortRegistry:
    _strategies = {}

    @classmethod
    def strategy(cls, name):
        def decorator(strategy_class):
            cls._strategies[name] = strategy_class()
            return strategy_class
        return decorator

    @classmethod
    def sort(cls, products, strategy, context=None):
        sorter = cls._strategies.get(strategy, cls._strategies["default"])
        return sorter.sort(products, context)

@SearchSortRegistry.strategy("relevance")
class RelevanceSort:
    def sort(self, products, ctx):
        return sorted(products, key=lambda p: p.relevance_score, reverse=True)

@SearchSortRegistry.strategy("price_low")
class PriceLowSort:
    def sort(self, products, ctx):
        return sorted(products, key=lambda p: p.price)

@SearchSortRegistry.strategy("price_high")
class PriceHighSort:
    def sort(self, products, ctx):
        return sorted(products, key=lambda p: p.price, reverse=True)

@SearchSortRegistry.strategy("rating")
class RatingSort:
    def sort(self, products, ctx):
        return sorted(products,
            key=lambda p: (p.avg_rating, p.review_count),
            reverse=True
        )

@SearchSortRegistry.strategy("newest")
class NewestSort:
    def sort(self, products, ctx):
        return sorted(products, key=lambda p: p.created_at, reverse=True)

@SearchSortRegistry.strategy("personalized")
class PersonalizedSort:
    def sort(self, products, ctx):
        prefs = ctx.preferences if ctx else []
        return sorted(products,
            key=lambda p: sum(p.tags.count(pref) for pref in prefs) + p.relevance_score,
            reverse=True
        )

@SearchSortRegistry.strategy("trending")
class TrendingSort:
    def sort(self, products, ctx):
        return sorted(products,
            key=lambda p: p.sales_last_7_days / max(p.days_listed, 1),
            reverse=True
        )

@SearchSortRegistry.strategy("default")
class DefaultSort:
    def sort(self, products, ctx): return products

SearchSortRegistry.sort(products, "personalized", context=user_context)
```

---

## 9.2 Graph Algorithm Registry
**Scenario:** Network topology analyzer — run different algorithms on infrastructure graph

**Imperative**
```python
def analyze_network(graph, algorithm, start_node=None):
    if algorithm == "bfs":
        visited = []
        queue   = deque([start_node])
        seen    = {start_node}
        while queue:
            node = queue.popleft()
            visited.append(node)
            for neighbor in graph[node]["connections"]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return visited

    elif algorithm == "shortest_path":
        distances = {node: float("inf") for node in graph}
        distances[start_node] = 0
        heap = [(0, start_node)]
        while heap:
            dist, node = heapq.heappop(heap)
            if dist > distances[node]:
                continue
            for neighbor, weight in graph[node]["connections"].items():
                new_dist = dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(heap, (new_dist, neighbor))
        return distances

    elif algorithm == "detect_cycles":
        visited   = set()
        rec_stack = set()
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]["connections"]:
                if neighbor not in visited:
                    if dfs(neighbor): return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False
        return any(dfs(n) for n in graph if n not in visited)

    elif algorithm == "connected_components":
        visited    = set()
        components = []
        def dfs_component(node, component):
            visited.add(node)
            component.append(node)
            for neighbor in graph[node]["connections"]:
                if neighbor not in visited:
                    dfs_component(neighbor, component)
        for node in graph:
            if node not in visited:
                component = []
                dfs_component(node, component)
                components.append(component)
        return components
```

**Declarative**
```python
class NetworkAnalyzerRegistry:
    _algorithms = {}

    @classmethod
    def algorithm(cls, name):
        def decorator(algo_class):
            cls._algorithms[name] = algo_class()
            return algo_class
        return decorator

    @classmethod
    def run(cls, graph, algorithm, **kwargs):
        algo = cls._algorithms.get(algorithm, cls._algorithms["default"])
        return algo.execute(graph, **kwargs)

@NetworkAnalyzerRegistry.algorithm("bfs")
class BFSAlgorithm:
    def execute(self, graph, start_node=None, **kwargs):
        visited, queue, seen = [], deque([start_node]), {start_node}
        while queue:
            node = queue.popleft()
            visited.append(node)
            queue.extend(
                n for n in graph[node]["connections"]
                if n not in seen and not seen.add(n)
            )
        return visited

@NetworkAnalyzerRegistry.algorithm("shortest_path")
class DijkstraAlgorithm:
    def execute(self, graph, start_node=None, **kwargs):
        distances          = {node: float("inf") for node in graph}
        distances[start_node] = 0
        heap               = [(0, start_node)]
        while heap:
            dist, node = heapq.heappop(heap)
            if dist > distances[node]:
                continue
            for neighbor, weight in graph[node]["connections"].items():
                new_dist = dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(heap, (new_dist, neighbor))
        return distances

@NetworkAnalyzerRegistry.algorithm("detect_cycles")
class CycleDetectionAlgorithm:
    def execute(self, graph, **kwargs):
        visited, rec_stack = set(), set()

        def visit(node):
            visited.add(node)
            rec_stack.add(node)
            found = any(
                n in rec_stack or (n not in visited and visit(n))
                for n in graph[node]["connections"]
            )
            rec_stack.discard(node)
            return found

        return any(visit(n) for n in graph if n not in visited)

@NetworkAnalyzerRegistry.algorithm("connected_components")
class ConnectedComponentsAlgorithm:
    def execute(self, graph, **kwargs):
        visited    = set()
        components = []

        def collect(node):
            visited.add(node)
            component = [node]
            component.extend(
                n for neighbor in graph[node]["connections"]
                if neighbor not in visited
                for n in collect(neighbor)
            )
            return component

        [components.append(collect(n)) for n in graph if n not in visited]
        return components

@NetworkAnalyzerRegistry.algorithm("default")
class NoopAlgorithm:
    def execute(self, graph, **kwargs): return []

NetworkAnalyzerRegistry.run(graph, "shortest_path", start_node="server_1")
```

---

## 9.3 Cache Eviction Registry
**Scenario:** Multi-tier cache system with pluggable eviction strategies

**Imperative**
```python
class Cache:
    def __init__(self, max_size, eviction_strategy):
        self.max_size          = max_size
        self.eviction_strategy = eviction_strategy
        self.store             = {}

    def set(self, key, value):
        if len(self.store) >= self.max_size:
            if self.eviction_strategy == "lru":
                oldest = min(self.store, key=lambda k: self.store[k]["last_accessed"])
                del self.store[oldest]
            elif self.eviction_strategy == "lfu":
                least  = min(self.store, key=lambda k: self.store[k]["access_count"])
                del self.store[least]
            elif self.eviction_strategy == "fifo":
                first  = min(self.store, key=lambda k: self.store[k]["inserted_at"])
                del self.store[first]
            elif self.eviction_strategy == "ttl":
                now     = time.time()
                expired = [k for k, v in self.store.items() if now > v["expires_at"]]
                for k in expired or [min(self.store, key=lambda k: self.store[k]["expires_at"])]:
                    del self.store[k]

        self.store[key] = {
            "value":        value,
            "last_accessed": time.time(),
            "access_count": 0,
            "inserted_at":  time.time(),
            "expires_at":   time.time() + 3600,
        }
```

**Declarative**
```python
class EvictionRegistry:
    _strategies = {}

    @classmethod
    def strategy(cls, name):
        def decorator(strategy_class):
            cls._strategies[name] = strategy_class()
            return strategy_class
        return decorator

    @classmethod
    def get(cls, name):
        return cls._strategies.get(name, cls._strategies["lru"])

class DeclarativeCache:
    def __init__(self, max_size, eviction_strategy="lru"):
        self._max_size = max_size
        self._strategy = EvictionRegistry.get(eviction_strategy)
        self._store    = {}

    def set(self, key, value):
        if len(self._store) >= self._max_size:
            self._strategy.evict(self._store)
        self._store[key] = self._strategy.make_entry(value)

    def get(self, key):
        if key in self._store:
            self._strategy.on_access(self._store[key])
        return self._store.get(key, {}).get("value")

@EvictionRegistry.strategy("lru")
class LRUStrategy:
    def make_entry(self, value):
        return {"value": value, "last_accessed": time.time()}
    def on_access(self, entry):
        entry["last_accessed"] = time.time()
    def evict(self, store):
        key = min(store, key=lambda k: store[k]["last_accessed"])
        del store[key]

@EvictionRegistry.strategy("lfu")
class LFUStrategy:
    def make_entry(self, value):
        return {"value": value, "access_count": 0}
    def on_access(self, entry):
        entry["access_count"] += 1
    def evict(self, store):
        key = min(store, key=lambda k: store[k]["access_count"])
        del store[key]

@EvictionRegistry.strategy("fifo")
class FIFOStrategy:
    def make_entry(self, value):
        return {"value": value, "inserted_at": time.time()}
    def on_access(self, entry): pass
    def evict(self, store):
        key = min(store, key=lambda k: store[k]["inserted_at"])
        del store[key]

@EvictionRegistry.strategy("ttl")
class TTLStrategy:
    def make_entry(self, value):
        return {"value": value, "expires_at": time.time() + 3600}
    def on_access(self, entry): pass
    def evict(self, store):
        now     = time.time()
        expired = [k for k, v in store.items() if now > v["expires_at"]]
        targets = expired or [min(store, key=lambda k: store[k]["expires_at"])]
        for k in targets:
            del store[k]

cache = DeclarativeCache(max_size=1000, eviction_strategy="lru")
cache.set("user:123", user_data)
```

---

## 9.4 Dependency Resolver
**Scenario:** Plugin system that boots in dependency order

**Imperative**
```python
_resolved = []
_seen     = set()

def resolve(name, registry):
    if name in _resolved:
        return
    if name in _seen:
        raise CircularDependencyError(f"Circular dependency: {name}")
    _seen.add(name)
    for dep in registry[name]["depends_on"]:
        resolve(dep, registry)
    _resolved.append(name)
    _seen.discard(name)

def boot_plugins(plugin_configs):
    global _resolved, _seen
    _resolved = []
    _seen     = set()

    for name in plugin_configs:
        resolve(name, plugin_configs)

    booted = []
    for name in _resolved:
        plugin = plugin_configs[name]["class"]()
        plugin.initialize()
        booted.append(plugin)

    return booted
```

**Declarative**
```python
class PluginRegistry:
    _plugins = {}

    @classmethod
    def register(cls, name, depends_on=None):
        def decorator(plugin_class):
            cls._plugins[name] = {
                "class":      plugin_class,
                "depends_on": depends_on or [],
            }
            return plugin_class
        return decorator

    @classmethod
    def boot_all(cls):
        order = cls._resolve_order()
        return [cls._boot_plugin(name) for name in order]

    @classmethod
    def _resolve_order(cls):
        resolved, seen = [], set()

        def visit(name):
            if name in resolved: return
            if name in seen:
                raise CircularDependencyError(f"Circular dependency: {name}")
            seen.add(name)
            [visit(dep) for dep in cls._plugins[name]["depends_on"]]
            resolved.append(name)
            seen.discard(name)

        [visit(name) for name in cls._plugins]
        return resolved

    @classmethod
    def _boot_plugin(cls, name):
        plugin = cls._plugins[name]["class"]()
        plugin.initialize()
        return plugin

@PluginRegistry.register("database", depends_on=[])
class DatabasePlugin:
    def initialize(self):
        self.connection = create_db_connection()

@PluginRegistry.register("cache", depends_on=["database"])
class CachePlugin:
    def initialize(self):
        self.redis = create_redis_connection()

@PluginRegistry.register("auth", depends_on=["database", "cache"])
class AuthPlugin:
    def initialize(self):
        self.jwt_secret = load_jwt_secret()

@PluginRegistry.register("api", depends_on=["auth", "database", "cache"])
class ApiPlugin:
    def initialize(self):
        self.router = setup_routes()

PluginRegistry.boot_all()
```

---

# CHAPTER 10 — Nested Structure Patterns

---

## 10.1 Nested Group-by
**Scenario:** Sales report grouped by region → country → product category

**Imperative**
```python
def group_sales(transactions):
    report = {}
    for tx in transactions:
        if tx.region not in report:
            report[tx.region] = {}
        if tx.country not in report[tx.region]:
            report[tx.region][tx.country] = {}
        if tx.category not in report[tx.region][tx.country]:
            report[tx.region][tx.country][tx.category] = {
                "total": 0, "count": 0, "transactions": []
            }
        bucket = report[tx.region][tx.country][tx.category]
        bucket["total"]        += tx.amount
        bucket["count"]        += 1
        bucket["transactions"].append(tx)
    return report
```

**Declarative**
```python
class NestedGroupRegistry:
    _group_keys   = []
    _leaf_reducer = None

    @classmethod
    def group_by(cls, key_fn):
        cls._group_keys.append(key_fn)
        return key_fn

    @classmethod
    def leaf(cls, fn):
        cls._leaf_reducer = fn
        return fn

    @classmethod
    def apply(cls, items):
        def group(data, key_fns):
            if not key_fns:
                return cls._leaf_reducer(list(data))
            key_fn, *rest = key_fns
            grouped = reduce(
                lambda acc, item: {
                    **acc,
                    key_fn(item): acc.get(key_fn(item), []) + [item]
                },
                data, {}
            )
            return {k: group(v, rest) for k, v in grouped.items()}
        return group(items, cls._group_keys)

@NestedGroupRegistry.group_by
def _(tx): return tx.region

@NestedGroupRegistry.group_by
def _(tx): return tx.country

@NestedGroupRegistry.group_by
def _(tx): return tx.category

@NestedGroupRegistry.leaf
def _(transactions):
    return {
        "total":        sum(tx.amount for tx in transactions),
        "count":        len(transactions),
        "transactions": transactions,
    }

NestedGroupRegistry.apply(transactions)
```

---

## 10.2 Deep Merge Registry
**Scenario:** Config system — merge base config, environment config, user overrides

**Imperative**
```python
def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            elif isinstance(result[key], set) and isinstance(value, set):
                result[key] = result[key] | value
            else:
                result[key] = value
        else:
            result[key] = value
    return result

def build_config(base, env_overrides, user_overrides):
    after_env  = deep_merge(base, env_overrides)
    after_user = deep_merge(after_env, user_overrides)
    return after_user
```

**Declarative**
```python
class MergeStrategyRegistry:
    _strategies = {}

    @classmethod
    def strategy(cls, type_pair):
        def decorator(fn):
            cls._strategies[type_pair] = fn
            return fn
        return decorator

    @classmethod
    def merge(cls, base, override):
        return reduce(
            lambda acc, pair: {
                **acc,
                pair[0]: cls._resolve(acc.get(pair[0]), pair[1])
            },
            override.items(),
            dict(base)
        )

    @classmethod
    def _resolve(cls, base_val, override_val):
        strategy = cls._strategies.get((type(base_val), type(override_val)))
        return strategy(base_val, override_val) if strategy else override_val

@MergeStrategyRegistry.strategy((dict, dict))
def _(base, override):
    return MergeStrategyRegistry.merge(base, override)

@MergeStrategyRegistry.strategy((list, list))
def _(base, override):
    return base + override

@MergeStrategyRegistry.strategy((set, set))
def _(base, override):
    return base | override

class ConfigBuilder:
    _layers = []

    @classmethod
    def layer(cls, fn):
        cls._layers.append(fn)
        return fn

    @classmethod
    def build(cls, sources):
        return reduce(
            MergeStrategyRegistry.merge,
            (layer(sources) for layer in cls._layers),
            {}
        )

@ConfigBuilder.layer
def base_config(sources): return sources["base"]

@ConfigBuilder.layer
def env_overrides(sources): return sources.get("env", {})

@ConfigBuilder.layer
def user_overrides(sources): return sources.get("user", {})

ConfigBuilder.build({
    "base": base_config,
    "env":  env_config,
    "user": user_config,
})
```

---

## 10.3 Tree Builder Registry
**Scenario:** Build a nested menu structure from a flat database result

**Imperative**
```python
def build_menu_tree(flat_items):
    # index all items
    nodes = {}
    for item in flat_items:
        nodes[item["id"]] = {
            **item,
            "children": [],
        }

    # attach children
    roots = []
    for item in flat_items:
        if item["parent_id"] is None:
            roots.append(nodes[item["id"]])
        else:
            if item["parent_id"] in nodes:
                nodes[item["parent_id"]]["children"].append(nodes[item["id"]])

    # sort each level
    def sort_node(node):
        node["children"].sort(key=lambda x: x["order"])
        for child in node["children"]:
            sort_node(child)
        return node

    roots.sort(key=lambda x: x["order"])
    return [sort_node(r) for r in roots]
```

**Declarative**
```python
class TreeBuilderRegistry:
    _id_fn       = None
    _parent_fn   = None
    _sort_fn     = None
    _node_builder = None

    @classmethod
    def id_field(cls, fn):
        cls._id_fn = fn
        return fn

    @classmethod
    def parent_field(cls, fn):
        cls._parent_fn = fn
        return fn

    @classmethod
    def sort_by(cls, fn):
        cls._sort_fn = fn
        return fn

    @classmethod
    def node(cls, fn):
        cls._node_builder = fn
        return fn

    @classmethod
    def build(cls, flat_items):
        nodes = reduce(
            lambda acc, item: {
                **acc,
                cls._id_fn(item): {**cls._node_builder(item), "children": []}
            },
            flat_items, {}
        )

        roots = []
        [
            roots.append(nodes[cls._id_fn(item)])
            if cls._parent_fn(item) is None
            else nodes[cls._parent_fn(item)]["children"].append(nodes[cls._id_fn(item)])
            for item in flat_items
            if cls._parent_fn(item) is None or cls._parent_fn(item) in nodes
        ]

        def sort_tree(node):
            node["children"].sort(key=cls._sort_fn)
            [sort_tree(c) for c in node["children"]]
            return node

        return [sort_tree(r) for r in sorted(roots, key=cls._sort_fn)]

@TreeBuilderRegistry.id_field
def _(item): return item["id"]

@TreeBuilderRegistry.parent_field
def _(item): return item["parent_id"]

@TreeBuilderRegistry.sort_by
def _(node): return node["order"]

@TreeBuilderRegistry.node
def _(item): return {
    "id":    item["id"],
    "label": item["label"],
    "url":   item["url"],
    "order": item["order"],
    "icon":  item.get("icon"),
}

TreeBuilderRegistry.build(flat_menu_items)
```

---

## 10.4 Recursive Diff Engine
**Scenario:** Config auditor — show exactly what changed between two configs

**Imperative**
```python
def diff(old, new, path=""):
    changes = []

    if type(old) != type(new):
        changes.append({"path": path, "type": "type_changed", "old": old, "new": new})
        return changes

    if isinstance(old, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            child_path = f"{path}.{key}" if path else key
            if key not in old:
                changes.append({"path": child_path, "type": "added", "value": new[key]})
            elif key not in new:
                changes.append({"path": child_path, "type": "removed", "value": old[key]})
            else:
                changes.extend(diff(old[key], new[key], child_path))

    elif isinstance(old, list):
        if len(old) != len(new):
            changes.append({"path": path, "type": "list_length_changed",
                            "old_len": len(old), "new_len": len(new)})
        for i, (o, n) in enumerate(zip(old, new)):
            changes.extend(diff(o, n, f"{path}[{i}]"))

    else:
        if old != new:
            changes.append({"path": path, "type": "changed", "old": old, "new": new})

    return changes
```

**Declarative**
```python
class DiffRegistry:
    _handlers = {}

    @classmethod
    def handles(cls, type_pair):
        def decorator(fn):
            cls._handlers[type_pair] = fn
            return fn
        return decorator

    @classmethod
    def diff(cls, old, new, path=""):
        if type(old) != type(new):
            return [{"path": path, "type": "type_changed", "old": old, "new": new}]
        handler = cls._handlers.get(type(old), cls._handlers["scalar"])
        return handler(old, new, path)

@DiffRegistry.handles(dict)
def _(old, new, path):
    all_keys   = set(old.keys()) | set(new.keys())
    child_path = lambda key: f"{path}.{key}" if path else key
    return reduce(
        lambda acc, key: acc + (
            [{"path": child_path(key), "type": "added",   "value": new[key]}] if key not in old else
            [{"path": child_path(key), "type": "removed", "value": old[key]}] if key not in new else
            DiffRegistry.diff(old[key], new[key], child_path(key))
        ),
        all_keys, []
    )

@DiffRegistry.handles(list)
def _(old, new, path):
    length_diffs = (
        [{"path": path, "type": "list_length_changed",
          "old_len": len(old), "new_len": len(new)}]
        if len(old) != len(new) else []
    )
    item_diffs = reduce(
        lambda acc, pair: acc + DiffRegistry.diff(pair[0], pair[1], f"{path}[{pair[2]}]"),
        [(o, n, i) for i, (o, n) in enumerate(zip(old, new))],
        []
    )
    return length_diffs + item_diffs

@DiffRegistry.handles("scalar")
def _(old, new, path):
    return [{"path": path, "type": "changed", "old": old, "new": new}] if old != new else []

DiffRegistry.diff(old_config, new_config)
```

---

## 10.5 Nested Pipeline
**Scenario:** Report generator — nested pipelines for sections, each section has its own pipeline

**Imperative**
```python
def generate_report(raw_data):
    # executive summary section
    summary_data   = filter_last_quarter(raw_data)
    summary_totals = compute_totals(summary_data)
    summary_trends = compute_trends(summary_data)
    summary        = {"totals": summary_totals, "trends": summary_trends}

    # detail section
    detail_data      = normalize_records(raw_data)
    detail_filtered  = filter_significant(detail_data)
    detail_sorted    = sort_by_impact(detail_filtered)
    detail_paginated = paginate(detail_sorted, page_size=50)

    # charts section
    chart_data     = aggregate_for_charts(raw_data)
    chart_monthly  = group_by_month(chart_data)
    chart_by_region = group_by_region(chart_data)

    return {
        "summary": summary,
        "details": detail_paginated,
        "charts":  {"monthly": chart_monthly, "by_region": chart_by_region},
    }
```

**Declarative**
```python
class SectionPipeline:
    def __init__(self, *stages):
        self._stages = list(stages)

    def run(self, data):
        return reduce(lambda d, stage: stage(d), self._stages, data)

class ReportPipeline:
    _sections = {}

    @classmethod
    def section(cls, name):
        def decorator(pipeline_class):
            cls._sections[name] = pipeline_class()
            return pipeline_class
        return decorator

    @classmethod
    def generate(cls, raw_data):
        return {
            name: section.run(raw_data)
            for name, section in cls._sections.items()
        }

@ReportPipeline.section("summary")
class SummarySection(SectionPipeline):
    def __init__(self):
        super().__init__(
            filter_last_quarter,
            lambda data: {
                "totals": compute_totals(data),
                "trends": compute_trends(data),
            }
        )

@ReportPipeline.section("details")
class DetailSection(SectionPipeline):
    def __init__(self):
        super().__init__(
            normalize_records,
            filter_significant,
            sort_by_impact,
            lambda data: paginate(data, page_size=50),
        )

@ReportPipeline.section("charts")
class ChartsSection(SectionPipeline):
    def __init__(self):
        super().__init__(
            aggregate_for_charts,
            lambda data: {
                "monthly":   group_by_month(data),
                "by_region": group_by_region(data),
            }
        )

ReportPipeline.generate(raw_data)
```
