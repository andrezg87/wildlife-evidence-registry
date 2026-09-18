CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('analyst', 'lab_director')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE species (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL,
    seized_part TEXT NOT NULL,
    unit TEXT NOT NULL CHECK (unit IN ('kg', 'unit')),
    reference_value_usd NUMERIC(12, 2) NOT NULL CHECK (reference_value_usd >= 0)
);

CREATE TABLE suspect (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    nationality TEXT NOT NULL
);

CREATE TABLE case_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_type TEXT NOT NULL CHECK (case_type IN ('airport_seizure', 'port_seizure', 'other_seizure')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'under_analysis', 'closed')),
    requesting_agency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE evidence_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_record (id),
    species_id UUID NOT NULL REFERENCES species (id),
    description TEXT NOT NULL,
    quantity NUMERIC(12, 3) NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL CHECK (unit IN ('kg', 'unit')),
    collection_date DATE NOT NULL,
    photo_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE case_suspect (
    case_id UUID NOT NULL REFERENCES case_record (id),
    suspect_id UUID NOT NULL REFERENCES suspect (id),
    role_in_case TEXT,
    PRIMARY KEY (case_id, suspect_id)
);

CREATE TABLE custody_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_item_id UUID NOT NULL REFERENCES evidence_item (id),
    recorded_by_user_id UUID NOT NULL REFERENCES users (id),
    handed_from TEXT NOT NULL,
    handed_to TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE monthly_report (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INT NOT NULL CHECK (year >= 2020),
    total_seizures INT NOT NULL,
    potential_loss_usd NUMERIC(14, 2) NOT NULL,
    potential_loss_sgd NUMERIC(14, 2) NOT NULL,
    most_affected_species TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved')),
    approved_by_user_id UUID REFERENCES users (id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (month, year)
);

CREATE TABLE monthly_report_translation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES monthly_report (id),
    language TEXT NOT NULL CHECK (language IN ('zh', 'ja', 'vi')),
    narrative_text TEXT NOT NULL,
    pdf_url TEXT,
    UNIQUE (report_id, language)
);
