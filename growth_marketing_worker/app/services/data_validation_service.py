class GrowthDataValidationService:
    REQUIRED_COLUMNS = {
        "products": [
            "merchant_id",
            "product_id",
            "sku",
            "product_name",
            "category",
            "subcategory",
            "brand",
            "price",
            "cost_price",
            "margin_percent",
            "target_segment",
            "customer_type",
            "inventory_count",
            "refund_rate_percent",
            "rating",
            "is_active",
            "launch_date",
            "source",
            "source_row_id",
        ],
        "sales": [
            "merchant_id",
            "order_id",
            "customer_id",
            "product_id",
            "sku",
            "quantity",
            "gross_revenue",
            "discount_amount",
            "refund_amount",
            "net_revenue",
            "customer_city",
            "locality",
            "pincode",
            "region",
            "customer_type",
            "order_date",
            "order_status",
            "payment_method",
            "source",
            "source_row_id",
        ],
        "campaigns": [
            "merchant_id",
            "campaign_id",
            "product_id",
            "sku",
            "campaign_name",
            "channel",
            "impressions",
            "clicks",
            "spend",
            "conversions",
            "attributed_revenue",
            "campaign_date",
            "post_time",
            "creative_type",
            "target_segment",
            "customer_city",
            "objective",
            "campaign_status",
            "source",
            "source_row_id",
        ],
        "customers": [
            "merchant_id",
            "customer_id",
            "customer_city",
            "locality",
            "pincode",
            "region",
            "customer_type",
            "age_group",
            "gender",
            "signup_date",
            "total_orders",
            "lifetime_value",
            "preferred_channel",
            "last_purchase_date",
            "source",
            "source_row_id",
        ],
        "content_calendar": [
            "merchant_id",
            "content_id",
            "campaign_id",
            "product_id",
            "sku",
            "channel",
            "content_type",
            "caption_angle",
            "scheduled_datetime",
            "published_datetime",
            "engagements",
            "likes",
            "comments",
            "shares",
            "saves",
            "clicks",
            "conversions",
            "status",
            "source",
            "source_row_id",
        ],
    }

    def validate_all(
        self,
        products_df,
        sales_df,
        campaigns_df,
        customers_df,
        content_df,
    ) -> dict:
        errors = []
        warnings = []

        dataframes = {
            "products": products_df,
            "sales": sales_df,
            "campaigns": campaigns_df,
            "customers": customers_df,
            "content_calendar": content_df,
        }

        for name, df in dataframes.items():
            errors.extend(self._validate_columns(name, df))
            errors.extend(self._validate_no_missing(name, df))

        errors.extend(self._validate_unique(products_df, "products", "product_id"))
        errors.extend(self._validate_unique(sales_df, "sales", "order_id"))
        errors.extend(self._validate_unique(campaigns_df, "campaigns", "campaign_id"))
        errors.extend(self._validate_unique(customers_df, "customers", "customer_id"))
        errors.extend(self._validate_unique(content_df, "content_calendar", "content_id"))

        errors.extend(self._validate_references(products_df, sales_df, campaigns_df, customers_df, content_df))
        errors.extend(self._validate_business_rules(products_df, sales_df, campaigns_df, content_df))

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "summary": {
                "row_counts": {
                    "products": len(products_df),
                    "sales": len(sales_df),
                    "campaigns": len(campaigns_df),
                    "customers": len(customers_df),
                    "content_calendar": len(content_df),
                }
            },
        }

    def _validate_columns(self, name, df):
        required = set(self.REQUIRED_COLUMNS[name])
        actual = set(df.columns)

        missing = required - actual
        extra = actual - required

        errors = []

        if missing:
            errors.append(f"{name}: missing columns -> {sorted(list(missing))}")

        if extra:
            errors.append(f"{name}: extra columns -> {sorted(list(extra))}")

        return errors

    def _validate_no_missing(self, name, df):
        errors = []

        if df.isna().sum().sum() > 0:
            missing_cols = df.columns[df.isna().any()].tolist()
            errors.append(f"{name}: contains NaN/missing values in columns -> {missing_cols}")

        empty_cols = []
        for col in df.columns:
            if df[col].astype(str).str.strip().eq("").any():
                empty_cols.append(col)

        if empty_cols:
            errors.append(f"{name}: contains empty string values in columns -> {empty_cols}")

        bad_tokens = ["nan", "none", "null"]
        bad_cols = []

        for col in df.columns:
            values = df[col].astype(str).str.strip().str.lower()
            if values.isin(bad_tokens).any():
                bad_cols.append(col)

        if bad_cols:
            errors.append(f"{name}: contains invalid tokens nan/none/null in columns -> {bad_cols}")

        return errors

    def _validate_unique(self, df, name, id_col):
        errors = []

        if id_col in df.columns and df[id_col].duplicated().any():
            duplicate_count = int(df[id_col].duplicated().sum())
            errors.append(f"{name}: duplicate {id_col} values -> {duplicate_count}")

        if "source_row_id" in df.columns and df["source_row_id"].duplicated().any():
            duplicate_count = int(df["source_row_id"].duplicated().sum())
            errors.append(f"{name}: duplicate source_row_id values -> {duplicate_count}")

        return errors

    def _validate_references(self, products_df, sales_df, campaigns_df, customers_df, content_df):
        errors = []

        product_ids = set(products_df["product_id"].astype(str))
        customer_ids = set(customers_df["customer_id"].astype(str))
        campaign_ids = set(campaigns_df["campaign_id"].astype(str))

        invalid_sales_products = ~sales_df["product_id"].astype(str).isin(product_ids)
        if invalid_sales_products.any():
            errors.append(f"sales: invalid product_id references -> {int(invalid_sales_products.sum())}")

        invalid_campaign_products = ~campaigns_df["product_id"].astype(str).isin(product_ids)
        if invalid_campaign_products.any():
            errors.append(f"campaigns: invalid product_id references -> {int(invalid_campaign_products.sum())}")

        invalid_content_products = ~content_df["product_id"].astype(str).isin(product_ids)
        if invalid_content_products.any():
            errors.append(f"content_calendar: invalid product_id references -> {int(invalid_content_products.sum())}")

        invalid_sales_customers = ~sales_df["customer_id"].astype(str).isin(customer_ids)
        if invalid_sales_customers.any():
            errors.append(f"sales: invalid customer_id references -> {int(invalid_sales_customers.sum())}")

        content_campaigns = content_df["campaign_id"].astype(str)
        invalid_content_campaigns = ~content_campaigns.isin(campaign_ids) & (content_campaigns != "NA")

        if invalid_content_campaigns.any():
            errors.append(f"content_calendar: invalid campaign_id references -> {int(invalid_content_campaigns.sum())}")

        return errors

    def _validate_business_rules(self, products_df, sales_df, campaigns_df, content_df):
        errors = []

        if (products_df["cost_price"] >= products_df["price"]).any():
            errors.append("products: cost_price must be less than price")

        if (sales_df["net_revenue"] < 0).any():
            errors.append("sales: net_revenue below 0 found")

        if (sales_df["refund_amount"] > sales_df["gross_revenue"]).any():
            errors.append("sales: refund_amount greater than gross_revenue found")

        if (campaigns_df["clicks"] > campaigns_df["impressions"]).any():
            errors.append("campaigns: clicks greater than impressions found")

        if (campaigns_df["conversions"] > campaigns_df["clicks"]).any():
            errors.append("campaigns: conversions greater than clicks found")

        if (content_df["clicks"] > content_df["engagements"]).any():
            errors.append("content_calendar: clicks greater than engagements found")

        if (content_df["conversions"] > content_df["clicks"]).any():
            errors.append("content_calendar: conversions greater than clicks found")

        return errors