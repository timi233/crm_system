--
-- PostgreSQL database dump
--

\restrict dpBFR5pxvkp7zIOcFo6s6pVoiNscSQdhLbM4QoSUeSBV73oyxeR1B0havggjZAm

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: businesstype; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.businesstype AS ENUM (
    'basic',
    'high_value',
    'pending_signup'
);


ALTER TYPE public.businesstype OWNER TO crm_user;

--
-- Name: channelstatus; Type: TYPE; Schema: public; Owner: crm_user
--

CREATE TYPE public.channelstatus AS ENUM (
    'active',
    'inactive',
    'suspended'
);


ALTER TYPE public.channelstatus OWNER TO crm_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_rules; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.alert_rules (
    id integer NOT NULL,
    rule_code character varying(50) NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_type character varying(30) NOT NULL,
    entity_type character varying(30) NOT NULL,
    priority character varying(10) DEFAULT 'medium'::character varying NOT NULL,
    threshold_days integer DEFAULT 0,
    threshold_amount integer DEFAULT 0,
    description text,
    is_active boolean DEFAULT true,
    created_at character varying(30),
    updated_at character varying(30)
);


ALTER TABLE public.alert_rules OWNER TO crm_user;

--
-- Name: alert_rules_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.alert_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_rules_id_seq OWNER TO crm_user;

--
-- Name: alert_rules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.alert_rules_id_seq OWNED BY public.alert_rules.id;


--
-- Name: auto_numbers; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.auto_numbers (
    id integer NOT NULL,
    entity_type character varying(20) NOT NULL,
    seq_date date NOT NULL,
    current_seq integer
);


ALTER TABLE public.auto_numbers OWNER TO crm_user;

--
-- Name: auto_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.auto_numbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auto_numbers_id_seq OWNER TO crm_user;

--
-- Name: auto_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.auto_numbers_id_seq OWNED BY public.auto_numbers.id;


--
-- Name: channel_assignments; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.channel_assignments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    channel_id integer NOT NULL,
    permission_level character varying(5) NOT NULL,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by integer,
    target_responsibility boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.channel_assignments OWNER TO crm_user;

--
-- Name: channel_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.channel_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.channel_assignments_id_seq OWNER TO crm_user;

--
-- Name: channel_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.channel_assignments_id_seq OWNED BY public.channel_assignments.id;


--
-- Name: channels; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.channels (
    id integer NOT NULL,
    channel_code character varying(30) NOT NULL,
    company_name character varying(255) NOT NULL,
    channel_type character varying(30) NOT NULL,
    status character varying(20),
    main_contact character varying(100),
    phone character varying(20),
    email character varying(100),
    province character varying(50),
    city character varying(50),
    address character varying(255),
    credit_code character varying(18),
    bank_name character varying(100),
    bank_account character varying(50),
    website character varying(255),
    wechat character varying(100),
    cooperation_products text,
    cooperation_region character varying(255),
    discount_rate numeric(5,4),
    billing_info text,
    notes text,
    created_at_legacy date,
    updated_at_legacy date,
    uuid_id uuid,
    business_type public.businesstype,
    channel_status public.channelstatus,
    description text,
    contact_person character varying(100),
    contact_email character varying(255),
    contact_phone character varying(50),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by integer,
    last_modified_by integer
);


ALTER TABLE public.channels OWNER TO crm_user;

--
-- Name: channels_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.channels_id_seq OWNER TO crm_user;

--
-- Name: channels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.channels_id_seq OWNED BY public.channels.id;


--
-- Name: contract_products; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.contract_products (
    id integer NOT NULL,
    contract_id integer NOT NULL,
    product_id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    quantity numeric(10,2) NOT NULL,
    unit_price numeric(15,2) NOT NULL,
    discount numeric(5,4),
    amount numeric(15,2) NOT NULL,
    notes text
);


ALTER TABLE public.contract_products OWNER TO crm_user;

--
-- Name: contract_products_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.contract_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contract_products_id_seq OWNER TO crm_user;

--
-- Name: contract_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.contract_products_id_seq OWNED BY public.contract_products.id;


--
-- Name: contracts; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.contracts (
    id integer NOT NULL,
    contract_code character varying(30) NOT NULL,
    contract_name character varying(255) NOT NULL,
    project_id integer NOT NULL,
    contract_direction character varying(20) NOT NULL,
    contract_status character varying(20) NOT NULL,
    terminal_customer_id integer,
    channel_id integer,
    contract_amount numeric(15,2) NOT NULL,
    signing_date date,
    effective_date date,
    expiry_date date,
    contract_file_url text,
    notes text,
    created_at date,
    updated_at date,
    CONSTRAINT chk_contract_direction CHECK (((contract_direction)::text = ANY ((ARRAY['Downstream'::character varying, 'Upstream'::character varying])::text[]))),
    CONSTRAINT chk_contract_status CHECK (((contract_status)::text = ANY ((ARRAY['draft'::character varying, 'pending'::character varying, 'signed'::character varying, 'archived'::character varying, 'rejected'::character varying])::text[])))
);


ALTER TABLE public.contracts OWNER TO crm_user;

--
-- Name: contracts_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.contracts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contracts_id_seq OWNER TO crm_user;

--
-- Name: contracts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.contracts_id_seq OWNED BY public.contracts.id;


--
-- Name: customer_channel_links; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.customer_channel_links (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    channel_id integer NOT NULL,
    role character varying(20) NOT NULL,
    discount_rate numeric(5,4),
    start_date date,
    end_date date,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by integer
);


ALTER TABLE public.customer_channel_links OWNER TO crm_user;

--
-- Name: customer_channel_links_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.customer_channel_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customer_channel_links_id_seq OWNER TO crm_user;

--
-- Name: customer_channel_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.customer_channel_links_id_seq OWNED BY public.customer_channel_links.id;


--
-- Name: dict_items; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.dict_items (
    id integer NOT NULL,
    dict_type character varying(50) NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    parent_id integer,
    sort_order integer,
    is_active boolean,
    extra_data json
);


ALTER TABLE public.dict_items OWNER TO crm_user;

--
-- Name: dict_items_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.dict_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dict_items_id_seq OWNER TO crm_user;

--
-- Name: dict_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.dict_items_id_seq OWNED BY public.dict_items.id;


--
-- Name: dispatch_records; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.dispatch_records (
    id integer NOT NULL,
    work_order_id character varying(100) NOT NULL,
    work_order_no character varying(50),
    source_type character varying(20) NOT NULL,
    lead_id integer,
    opportunity_id integer,
    project_id integer,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    previous_status character varying(50),
    status_updated_at timestamp with time zone,
    order_type character varying(10),
    customer_name character varying(255),
    technician_ids text[],
    priority character varying(20),
    description text,
    dispatch_data jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    dispatched_at timestamp with time zone,
    completed_at timestamp with time zone,
    CONSTRAINT check_source_type CHECK (((source_type)::text = ANY ((ARRAY['lead'::character varying, 'opportunity'::character varying, 'project'::character varying])::text[])))
);


ALTER TABLE public.dispatch_records OWNER TO crm_user;

--
-- Name: dispatch_records_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.dispatch_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dispatch_records_id_seq OWNER TO crm_user;

--
-- Name: dispatch_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.dispatch_records_id_seq OWNED BY public.dispatch_records.id;


--
-- Name: evaluations; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.evaluations (
    id integer NOT NULL,
    work_order_id integer NOT NULL,
    quality_rating integer NOT NULL,
    response_rating integer NOT NULL,
    customer_feedback text,
    improvement_suggestion text,
    recommend boolean NOT NULL,
    evaluator_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.evaluations OWNER TO crm_user;

--
-- Name: evaluations_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.evaluations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.evaluations_id_seq OWNER TO crm_user;

--
-- Name: evaluations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.evaluations_id_seq OWNED BY public.evaluations.id;


--
-- Name: execution_plans; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.execution_plans (
    id integer NOT NULL,
    channel_id integer NOT NULL,
    user_id integer NOT NULL,
    plan_type character varying(7) NOT NULL,
    plan_period character varying(20) NOT NULL,
    plan_content text NOT NULL,
    execution_status text,
    key_obstacles text,
    next_steps text,
    status character varying(11) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.execution_plans OWNER TO crm_user;

--
-- Name: execution_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.execution_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.execution_plans_id_seq OWNER TO crm_user;

--
-- Name: execution_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.execution_plans_id_seq OWNED BY public.execution_plans.id;


--
-- Name: follow_ups; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.follow_ups (
    id integer NOT NULL,
    terminal_customer_id integer,
    lead_id integer,
    opportunity_id integer,
    project_id integer,
    follow_up_date date NOT NULL,
    follow_up_method character varying(30) NOT NULL,
    follow_up_content text NOT NULL,
    follow_up_conclusion character varying(30) NOT NULL,
    next_action character varying(255),
    next_follow_up_date date,
    follower_id integer NOT NULL,
    created_at date
);


ALTER TABLE public.follow_ups OWNER TO crm_user;

--
-- Name: follow_ups_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.follow_ups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.follow_ups_id_seq OWNER TO crm_user;

--
-- Name: follow_ups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.follow_ups_id_seq OWNED BY public.follow_ups.id;


--
-- Name: knowledge; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.knowledge (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    problem_type character varying(100),
    problem text NOT NULL,
    solution text NOT NULL,
    tags character varying[],
    source_type character varying(10) NOT NULL,
    source_id integer,
    view_count integer NOT NULL,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.knowledge OWNER TO crm_user;

--
-- Name: knowledge_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.knowledge_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.knowledge_id_seq OWNER TO crm_user;

--
-- Name: knowledge_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.knowledge_id_seq OWNED BY public.knowledge.id;


--
-- Name: leads; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.leads (
    id integer NOT NULL,
    lead_code character varying(25) NOT NULL,
    lead_name character varying(255) NOT NULL,
    terminal_customer_id integer NOT NULL,
    channel_id integer,
    source_channel_id integer,
    lead_stage character varying(30) NOT NULL,
    lead_source character varying(50),
    contact_person character varying(100),
    contact_phone character varying(20),
    products character varying(100)[],
    estimated_budget numeric(15,2),
    has_confirmed_requirement boolean,
    has_confirmed_budget boolean,
    converted_to_opportunity boolean,
    opportunity_id integer,
    sales_owner_id integer NOT NULL,
    notes text,
    created_at date,
    updated_at date
);


ALTER TABLE public.leads OWNER TO crm_user;

--
-- Name: leads_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.leads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.leads_id_seq OWNER TO crm_user;

--
-- Name: leads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.leads_id_seq OWNED BY public.leads.id;


--
-- Name: nine_a; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.nine_a (
    id integer NOT NULL,
    opportunity_id integer NOT NULL,
    key_events text,
    budget numeric(15,2),
    decision_chain_influence text,
    customer_challenges text,
    customer_needs text,
    solution_differentiation text,
    competitors text,
    buying_method text,
    close_date date
);


ALTER TABLE public.nine_a OWNER TO crm_user;

--
-- Name: nine_a_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.nine_a_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nine_a_id_seq OWNER TO crm_user;

--
-- Name: nine_a_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.nine_a_id_seq OWNED BY public.nine_a.id;


--
-- Name: nine_a_versions; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.nine_a_versions (
    id integer NOT NULL,
    opportunity_id integer NOT NULL,
    version_number integer NOT NULL,
    key_events text,
    budget numeric(15,2),
    decision_chain_influence text,
    customer_challenges text,
    customer_needs text,
    solution_differentiation text,
    competitors text,
    buying_method text,
    close_date date,
    created_at timestamp without time zone DEFAULT now(),
    created_by_id integer
);


ALTER TABLE public.nine_a_versions OWNER TO crm_user;

--
-- Name: nine_a_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.nine_a_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nine_a_versions_id_seq OWNER TO crm_user;

--
-- Name: nine_a_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.nine_a_versions_id_seq OWNED BY public.nine_a_versions.id;


--
-- Name: operation_logs; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.operation_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    user_name character varying(100) NOT NULL,
    action_type character varying(30) NOT NULL,
    entity_type character varying(30) NOT NULL,
    entity_id integer NOT NULL,
    entity_code character varying(30),
    entity_name character varying(255),
    old_value jsonb,
    new_value jsonb,
    description text,
    ip_address character varying(45),
    created_at timestamp without time zone
);


ALTER TABLE public.operation_logs OWNER TO crm_user;

--
-- Name: operation_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.operation_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.operation_logs_id_seq OWNER TO crm_user;

--
-- Name: operation_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.operation_logs_id_seq OWNED BY public.operation_logs.id;


--
-- Name: opportunities; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.opportunities (
    id integer NOT NULL,
    opportunity_code character varying(50) NOT NULL,
    opportunity_name character varying(255) NOT NULL,
    terminal_customer_id integer NOT NULL,
    opportunity_source character varying(50) NOT NULL,
    product_ids integer[],
    products character varying(100)[],
    opportunity_stage character varying(30) NOT NULL,
    expected_contract_amount numeric(15,2) NOT NULL,
    expected_close_date date,
    sales_owner_id integer NOT NULL,
    channel_id integer,
    vendor_registration_status character varying(30),
    vendor_discount numeric(5,4),
    loss_reason character varying(100),
    project_id integer,
    created_at date,
    CONSTRAINT chk_loss_reason CHECK ((((opportunity_stage)::text <> 'Lost'::text) OR (loss_reason IS NOT NULL)))
);


ALTER TABLE public.opportunities OWNER TO crm_user;

--
-- Name: opportunities_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.opportunities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.opportunities_id_seq OWNER TO crm_user;

--
-- Name: opportunities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.opportunities_id_seq OWNED BY public.opportunities.id;


--
-- Name: payment_plans; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.payment_plans (
    id integer NOT NULL,
    contract_id integer NOT NULL,
    plan_stage character varying(50) NOT NULL,
    plan_amount numeric(15,2) NOT NULL,
    plan_date date,
    actual_amount numeric(15,2),
    actual_date date,
    payment_status character varying(20),
    notes text,
    CONSTRAINT chk_payment_status CHECK (((payment_status)::text = ANY ((ARRAY['pending'::character varying, 'partial'::character varying, 'completed'::character varying])::text[])))
);


ALTER TABLE public.payment_plans OWNER TO crm_user;

--
-- Name: payment_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.payment_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payment_plans_id_seq OWNER TO crm_user;

--
-- Name: payment_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.payment_plans_id_seq OWNED BY public.payment_plans.id;


--
-- Name: product_installations; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.product_installations (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    manufacturer character varying(100) NOT NULL,
    product_type character varying(100) NOT NULL,
    product_model character varying(100),
    license_scale character varying(100),
    system_version character varying(100),
    online_date date,
    maintenance_expiry date,
    username character varying(255),
    password character varying(255),
    login_url character varying(255),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_id integer,
    CONSTRAINT check_manufacturer CHECK (((manufacturer)::text = ANY ((ARRAY['爱数'::character varying, '安恒'::character varying, 'IPG'::character varying, '绿盟'::character varying, '深信服'::character varying, '其他'::character varying])::text[])))
);


ALTER TABLE public.product_installations OWNER TO crm_user;

--
-- Name: product_installations_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.product_installations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_installations_id_seq OWNER TO crm_user;

--
-- Name: product_installations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.product_installations_id_seq OWNED BY public.product_installations.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.products (
    id integer NOT NULL,
    product_code character varying(10) NOT NULL,
    product_name character varying(100) NOT NULL,
    product_type character varying(30) NOT NULL,
    brand_manufacturer character varying(100) NOT NULL,
    is_active boolean,
    notes text
);


ALTER TABLE public.products OWNER TO crm_user;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO crm_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    project_code character varying(25) NOT NULL,
    project_name character varying(255) NOT NULL,
    terminal_customer_id integer NOT NULL,
    channel_id integer,
    source_opportunity_id integer,
    product_ids integer[] NOT NULL,
    products character varying(100)[],
    business_type character varying(30) NOT NULL,
    project_status character varying(30) NOT NULL,
    sales_owner_id integer NOT NULL,
    downstream_contract_amount numeric(15,2) NOT NULL,
    upstream_procurement_amount numeric(15,2),
    direct_project_investment numeric(15,2),
    additional_investment numeric(15,2),
    winning_date date,
    acceptance_date date,
    first_payment_date date,
    actual_payment_amount numeric(15,2),
    notes text,
    gross_margin numeric(15,2)
);


ALTER TABLE public.projects OWNER TO crm_user;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projects_id_seq OWNER TO crm_user;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: sales_targets; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.sales_targets (
    id integer NOT NULL,
    user_id integer NOT NULL,
    target_type character varying(20) NOT NULL,
    target_year integer NOT NULL,
    target_period integer NOT NULL,
    target_amount double precision NOT NULL,
    parent_id integer,
    created_at date,
    updated_at date
);


ALTER TABLE public.sales_targets OWNER TO crm_user;

--
-- Name: sales_targets_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.sales_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_targets_id_seq OWNER TO crm_user;

--
-- Name: sales_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.sales_targets_id_seq OWNED BY public.sales_targets.id;


--
-- Name: terminal_customers; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.terminal_customers (
    id integer NOT NULL,
    customer_code character varying(50) NOT NULL,
    customer_name character varying(255) NOT NULL,
    credit_code character varying(18) NOT NULL,
    customer_industry character varying(50) NOT NULL,
    customer_region character varying(100) NOT NULL,
    customer_owner_id integer NOT NULL,
    channel_id integer,
    main_contact character varying(100),
    phone character varying(20),
    customer_status character varying(20) NOT NULL,
    maintenance_expiry date,
    notes text
);


ALTER TABLE public.terminal_customers OWNER TO crm_user;

--
-- Name: terminal_customers_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.terminal_customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.terminal_customers_id_seq OWNER TO crm_user;

--
-- Name: terminal_customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.terminal_customers_id_seq OWNED BY public.terminal_customers.id;


--
-- Name: unified_targets; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.unified_targets (
    id integer NOT NULL,
    target_type character varying(7) NOT NULL,
    channel_id integer,
    user_id integer,
    year integer NOT NULL,
    quarter integer,
    month integer,
    performance_target numeric(10,2),
    opportunity_target numeric(10,2),
    project_count_target integer,
    development_goal text,
    achieved_performance numeric(10,2),
    achieved_opportunity numeric(10,2),
    achieved_project_count integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by integer
);


ALTER TABLE public.unified_targets OWNER TO crm_user;

--
-- Name: unified_targets_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.unified_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unified_targets_id_seq OWNER TO crm_user;

--
-- Name: unified_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.unified_targets_id_seq OWNED BY public.unified_targets.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying,
    hashed_password character varying,
    is_active boolean,
    role character varying NOT NULL,
    name character varying,
    feishu_id character varying,
    phone character varying,
    avatar text,
    sales_leader_id integer,
    sales_region character varying,
    sales_product_line character varying,
    uuid_id uuid,
    cuid_id character varying(255),
    functional_role character varying(50),
    responsibility_role character varying(50),
    department character varying(100),
    user_status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    full_name character varying(255)
);


ALTER TABLE public.users OWNER TO crm_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO crm_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: work_order_technicians; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.work_order_technicians (
    id integer NOT NULL,
    work_order_id integer NOT NULL,
    technician_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.work_order_technicians OWNER TO crm_user;

--
-- Name: work_order_technicians_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.work_order_technicians_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.work_order_technicians_id_seq OWNER TO crm_user;

--
-- Name: work_order_technicians_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.work_order_technicians_id_seq OWNED BY public.work_order_technicians.id;


--
-- Name: work_orders; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.work_orders (
    id integer NOT NULL,
    cuid_id character varying(50),
    work_order_no character varying(50) NOT NULL,
    order_type character varying(2) NOT NULL,
    submitter_id integer NOT NULL,
    related_sales_id integer,
    customer_name character varying(255) NOT NULL,
    customer_contact character varying(100),
    customer_phone character varying(50),
    has_channel boolean NOT NULL,
    channel_id integer,
    channel_name character varying(100),
    channel_contact character varying(100),
    channel_phone character varying(50),
    manufacturer_contact character varying(100),
    work_type character varying(50),
    priority character varying(11) NOT NULL,
    description text NOT NULL,
    status character varying(10) NOT NULL,
    estimated_start_date date,
    estimated_start_period character varying(10),
    estimated_end_date date,
    estimated_end_period character varying(10),
    accepted_at timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    service_summary text,
    cancel_reason text,
    source_type character varying(11),
    lead_id integer,
    opportunity_id integer,
    project_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.work_orders OWNER TO crm_user;

--
-- Name: work_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: crm_user
--

CREATE SEQUENCE public.work_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.work_orders_id_seq OWNER TO crm_user;

--
-- Name: work_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crm_user
--

ALTER SEQUENCE public.work_orders_id_seq OWNED BY public.work_orders.id;


--
-- Name: alert_rules id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.alert_rules ALTER COLUMN id SET DEFAULT nextval('public.alert_rules_id_seq'::regclass);


--
-- Name: auto_numbers id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.auto_numbers ALTER COLUMN id SET DEFAULT nextval('public.auto_numbers_id_seq'::regclass);


--
-- Name: channel_assignments id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.channel_assignments ALTER COLUMN id SET DEFAULT nextval('public.channel_assignments_id_seq'::regclass);


--
-- Name: channels id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.channels ALTER COLUMN id SET DEFAULT nextval('public.channels_id_seq'::regclass);


--
-- Name: contract_products id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contract_products ALTER COLUMN id SET DEFAULT nextval('public.contract_products_id_seq'::regclass);


--
-- Name: contracts id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contracts ALTER COLUMN id SET DEFAULT nextval('public.contracts_id_seq'::regclass);


--
-- Name: customer_channel_links id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.customer_channel_links ALTER COLUMN id SET DEFAULT nextval('public.customer_channel_links_id_seq'::regclass);


--
-- Name: dict_items id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dict_items ALTER COLUMN id SET DEFAULT nextval('public.dict_items_id_seq'::regclass);


--
-- Name: dispatch_records id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records ALTER COLUMN id SET DEFAULT nextval('public.dispatch_records_id_seq'::regclass);


--
-- Name: evaluations id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.evaluations ALTER COLUMN id SET DEFAULT nextval('public.evaluations_id_seq'::regclass);


--
-- Name: execution_plans id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.execution_plans ALTER COLUMN id SET DEFAULT nextval('public.execution_plans_id_seq'::regclass);


--
-- Name: follow_ups id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups ALTER COLUMN id SET DEFAULT nextval('public.follow_ups_id_seq'::regclass);


--
-- Name: knowledge id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.knowledge ALTER COLUMN id SET DEFAULT nextval('public.knowledge_id_seq'::regclass);


--
-- Name: leads id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads ALTER COLUMN id SET DEFAULT nextval('public.leads_id_seq'::regclass);


--
-- Name: nine_a id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a ALTER COLUMN id SET DEFAULT nextval('public.nine_a_id_seq'::regclass);


--
-- Name: nine_a_versions id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a_versions ALTER COLUMN id SET DEFAULT nextval('public.nine_a_versions_id_seq'::regclass);


--
-- Name: operation_logs id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.operation_logs ALTER COLUMN id SET DEFAULT nextval('public.operation_logs_id_seq'::regclass);


--
-- Name: opportunities id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.opportunities ALTER COLUMN id SET DEFAULT nextval('public.opportunities_id_seq'::regclass);


--
-- Name: payment_plans id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.payment_plans ALTER COLUMN id SET DEFAULT nextval('public.payment_plans_id_seq'::regclass);


--
-- Name: product_installations id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.product_installations ALTER COLUMN id SET DEFAULT nextval('public.product_installations_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: sales_targets id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.sales_targets ALTER COLUMN id SET DEFAULT nextval('public.sales_targets_id_seq'::regclass);


--
-- Name: terminal_customers id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.terminal_customers ALTER COLUMN id SET DEFAULT nextval('public.terminal_customers_id_seq'::regclass);


--
-- Name: unified_targets id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.unified_targets ALTER COLUMN id SET DEFAULT nextval('public.unified_targets_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: work_order_technicians id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_order_technicians ALTER COLUMN id SET DEFAULT nextval('public.work_order_technicians_id_seq'::regclass);


--
-- Name: work_orders id; Type: DEFAULT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders ALTER COLUMN id SET DEFAULT nextval('public.work_orders_id_seq'::regclass);


--
-- Data for Name: alert_rules; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.alert_rules (id, rule_code, rule_name, rule_type, entity_type, priority, threshold_days, threshold_amount, description, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: auto_numbers; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.auto_numbers (id, entity_type, seq_date, current_seq) FROM stdin;
10	PRJ	2026-04-18	2
9	OPP	2026-04-18	2
11	CHAN	2026-04-18	1
3	CUST	2026-04-22	1
4	LEAD	2026-04-22	1
\.


--
-- Data for Name: channel_assignments; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.channel_assignments (id, user_id, channel_id, permission_level, assigned_at, assigned_by, target_responsibility, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: channels; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.channels (id, channel_code, company_name, channel_type, status, main_contact, phone, email, province, city, address, credit_code, bank_name, bank_account, website, wechat, cooperation_products, cooperation_region, discount_rate, billing_info, notes, created_at_legacy, updated_at_legacy, uuid_id, business_type, channel_status, description, contact_person, contact_email, contact_phone, created_at, updated_at, created_by, last_modified_by) FROM stdin;
1	PYCRM-CHAN-20260418-001	测试渠道	代理商	活跃	测试渠道联系人	2222222222222	\N	山东省	烟台市	\N	333333333333333333	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2026-04-18 14:31:13.515357+00	\N	2	\N
\.


--
-- Data for Name: contract_products; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.contract_products (id, contract_id, product_id, product_name, quantity, unit_price, discount, amount, notes) FROM stdin;
\.


--
-- Data for Name: contracts; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.contracts (id, contract_code, contract_name, project_id, contract_direction, contract_status, terminal_customer_id, channel_id, contract_amount, signing_date, effective_date, expiry_date, contract_file_url, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: customer_channel_links; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.customer_channel_links (id, customer_id, channel_id, role, discount_rate, start_date, end_date, notes, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: dict_items; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.dict_items (id, dict_type, code, name, parent_id, sort_order, is_active, extra_data) FROM stdin;
1	地区	37	山东省	\N	1	t	\N
101	地区	3701	济南市	1	1	t	\N
102	地区	3702	青岛市	1	2	t	\N
103	地区	3703	淄博市	1	3	t	\N
104	地区	3704	枣庄市	1	4	t	\N
105	地区	3705	东营市	1	5	t	\N
106	地区	3706	烟台市	1	6	t	\N
107	地区	3707	潍坊市	1	7	t	\N
108	地区	3708	济宁市	1	8	t	\N
109	地区	3709	泰安市	1	9	t	\N
110	地区	3710	威海市	1	10	t	\N
111	地区	3711	日照市	1	11	t	\N
112	地区	3713	临沂市	1	12	t	\N
113	地区	3714	德州市	1	13	t	\N
114	地区	3715	聊城市	1	14	t	\N
115	地区	3716	滨州市	1	15	t	\N
116	地区	3717	菏泽市	1	16	t	\N
2	行业	GOV	政府单位	\N	1	t	\N
3	行业	PSU	事业单位	\N	2	t	\N
4	行业	OTHER	其他	\N	3	t	\N
5	行业	MFG	制造	\N	4	t	\N
6	行业	CHEM	化工	\N	5	t	\N
7	行业	PHA	医药	\N	6	t	\N
8	行业	ENER	能源	\N	7	t	\N
9	行业	AUTO	汽车	\N	8	t	\N
10	行业	CHIP	芯片	\N	9	t	\N
11	行业	IT	信息技术	\N	10	t	\N
12	行业	FIN	金融	\N	11	t	\N
13	行业	EDU	教育	\N	12	t	\N
14	行业	HEALTH	医疗	\N	13	t	\N
15	行业	RETAIL	零售	\N	14	t	\N
16	行业	LOGST	物流	\N	15	t	\N
17	行业	CONST	建筑	\N	16	t	\N
18	行业	AGRI	农业	\N	17	t	\N
19	行业	TELECOM	通信	\N	18	t	\N
20	行业	MEDIA	传媒	\N	19	t	\N
21	商机来源	REF	客户推荐	\N	1	t	\N
22	商机来源	WEB	网络推广	\N	2	t	\N
23	商机来源	EXPO	展会	\N	3	t	\N
24	商机来源	CALL	电话营销	\N	4	t	\N
25	商机来源	EXIST	老客户二次开发	\N	5	t	\N
26	商机来源	PART	合作伙伴推荐	\N	6	t	\N
27	客户状态	POTENTIAL	潜在	\N	1	t	\N
28	客户状态	ACTIVE	活跃	\N	2	t	\N
29	客户状态	CONTRACTED	已签约	\N	3	t	\N
30	客户状态	DORMANT	休眠	\N	4	t	\N
31	客户状态	CHURNED	流失	\N	5	t	\N
32	跟进方式	phone	电话沟通	\N	1	t	\N
33	跟进方式	wechat	微信沟通	\N	2	t	\N
34	跟进方式	email	邮件沟通	\N	3	t	\N
35	跟进方式	visit	上门拜访	\N	4	t	\N
36	跟进方式	meeting	会议交流	\N	5	t	\N
37	跟进方式	demo	产品演示	\N	6	t	\N
38	跟进方式	proposal	方案报价	\N	7	t	\N
39	跟进方式	contract	合同洽谈	\N	8	t	\N
40	跟进方式	other	其他方式	\N	9	t	\N
41	跟进结论	positive	有意向	\N	1	t	\N
42	跟进结论	pending	待进一步沟通	\N	2	t	\N
43	跟进结论	negotiating	商务谈判中	\N	3	t	\N
44	跟进结论	quoted	已报价待反馈	\N	4	t	\N
45	跟进结论	confirmed	已确认需求	\N	5	t	\N
46	跟进结论	signed	已签约	\N	6	t	\N
47	跟进结论	rejected	暂无意向	\N	7	t	\N
48	跟进结论	lost	已流失	\N	8	t	\N
49	跟进结论	follow_up	需持续跟进	\N	9	t	\N
50	product_type	server	服务器	\N	1	t	\N
51	product_type	storage	存储设备	\N	2	t	\N
52	product_type	network	网络设备	\N	3	t	\N
53	product_type	software	软件系统	\N	4	t	\N
54	product_type	security	安全设备	\N	5	t	\N
55	brand	dell	Dell	50	1	t	\N
56	brand	hp	HP	50	2	t	\N
57	brand	lenovo	联想	50	3	t	\N
58	brand	huawei	华为	50	4	t	\N
59	brand	netapp	NetApp	51	1	t	\N
60	brand	dellemc	Dell EMC	51	2	t	\N
61	model	dell_r740	Dell PowerEdge R740	55	1	t	\N
62	model	dell_r750	Dell PowerEdge R750	55	2	t	\N
63	model	dell_r940	Dell PowerEdge R940	55	3	t	\N
64	model	hp_dl380	HP ProLiant DL380	56	1	t	\N
65	model	hp_dl360	HP ProLiant DL360	56	2	t	\N
66	model	netapp_fas	NetApp FAS系列	59	1	t	\N
67	model	dellemc_powervault	Dell EMC PowerVault	60	1	t	\N
117	产品品牌	dell	Dell	50	1	t	\N
118	产品品牌	hp	HP	50	2	t	\N
119	产品品牌	lenovo	联想	50	3	t	\N
120	产品品牌	huawei	华为	50	4	t	\N
121	产品品牌	netapp	NetApp	51	1	t	\N
122	产品品牌	dellemc	Dell EMC	51	2	t	\N
123	商机阶段	new	新建	\N	1	t	\N
124	商机阶段	contacted	已联系	\N	2	t	\N
125	商机阶段	qualified	已验证	\N	3	t	\N
126	商机阶段	proposal	方案报价	\N	4	t	\N
127	商机阶段	negotiation	商务谈判	\N	5	t	\N
128	商机阶段	won	成交	\N	6	t	\N
129	商机阶段	lost	失败	\N	7	t	\N
130	渠道类型	direct	直销	\N	1	t	\N
131	渠道类型	agent	代理商	\N	2	t	\N
132	渠道类型	partner	合作伙伴	\N	3	t	\N
133	渠道类型	online	线上渠道	\N	4	t	\N
134	渠道状态	active	活跃	\N	1	t	\N
135	渠道状态	inactive	非活跃	\N	2	t	\N
136	渠道状态	pending	待审核	\N	3	t	\N
137	项目状态	draft	草稿	\N	1	t	\N
138	项目状态	submitted	已提交	\N	2	t	\N
139	项目状态	approved	已批准	\N	3	t	\N
140	项目状态	executing	执行中	\N	4	t	\N
141	项目状态	completed	已完成	\N	5	t	\N
142	项目状态	cancelled	已取消	\N	6	t	\N
143	制造商	爱数	爱数	\N	1	t	\N
144	制造商	安恒	安恒	\N	2	t	\N
145	制造商	IPG	IPG	\N	3	t	\N
146	制造商	绿盟	绿盟	\N	4	t	\N
147	制造商	深信服	深信服	\N	5	t	\N
148	制造商	其他	其他	\N	6	t	\N
149	产品装机产品类型	anyshare	AnyShare	\N	1	t	\N
150	产品装机产品类型	anybackup	AnyBackup	\N	2	t	\N
151	产品装机产品类型	dbaudit	数据库审计	\N	3	t	\N
152	产品装机产品类型	waf	WAF	\N	4	t	\N
153	产品装机产品类型	ids	IDS	\N	5	t	\N
154	产品装机产品类型	ips	IPS	\N	6	t	\N
155	产品装机产品类型	firewall	防火墙	\N	7	t	\N
156	产品装机产品类型	sslvpn	SSL VPN	\N	8	t	\N
157	产品装机产品类型	其他	其他	\N	9	t	\N
158	产品类型	server	服务器	\N	1	t	\N
159	产品类型	storage	存储设备	\N	2	t	\N
160	产品类型	network	网络设备	\N	3	t	\N
161	产品类型	software	软件系统	\N	4	t	\N
162	产品类型	security	安全设备	\N	5	t	\N
\.


--
-- Data for Name: dispatch_records; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.dispatch_records (id, work_order_id, work_order_no, source_type, lead_id, opportunity_id, project_id, status, previous_status, status_updated_at, order_type, customer_name, technician_ids, priority, description, dispatch_data, created_at, updated_at, dispatched_at, completed_at) FROM stdin;
\.


--
-- Data for Name: evaluations; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.evaluations (id, work_order_id, quality_rating, response_rating, customer_feedback, improvement_suggestion, recommend, evaluator_id, created_at) FROM stdin;
\.


--
-- Data for Name: execution_plans; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.execution_plans (id, channel_id, user_id, plan_type, plan_period, plan_content, execution_status, key_obstacles, next_steps, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: follow_ups; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.follow_ups (id, terminal_customer_id, lead_id, opportunity_id, project_id, follow_up_date, follow_up_method, follow_up_content, follow_up_conclusion, next_action, next_follow_up_date, follower_id, created_at) FROM stdin;
1	1	1	\N	\N	2026-04-18	电话沟通	1231	有意向	\N	2026-04-20	2	2026-04-18
2	1	\N	2	\N	2026-04-18	上门拜访	jkhk	待进一步沟通	\N	2026-04-23	2	2026-04-18
3	1	\N	\N	2	2026-04-22	上门拜访	1312	已报价待反馈	\N	2026-04-22	2	2026-04-18
4	6	2	\N	\N	2026-04-22	电话沟通	电话邀约，打算登门致歉，上门查看问题，解决问题，提高客户满意度，做好客户关系，参与换新项目	待进一步沟通	上门拜访	2026-04-23	3	2026-04-22
\.


--
-- Data for Name: knowledge; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.knowledge (id, title, problem_type, problem, solution, tags, source_type, source_id, view_count, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: leads; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.leads (id, lead_code, lead_name, terminal_customer_id, channel_id, source_channel_id, lead_stage, lead_source, contact_person, contact_phone, products, estimated_budget, has_confirmed_requirement, has_confirmed_budget, converted_to_opportunity, opportunity_id, sales_owner_id, notes, created_at, updated_at) FROM stdin;
1	PYCRM-LEAD-20260418-001	ces	1	1	\N	初步接触	地推陌拜	\N	\N	{}	\N	f	f	f	\N	2	\N	2026-04-18	2026-04-18
2	PYCRM-LEAD-20260422-001	日审换新	6	\N	\N	初步接触	电话营销	于欣尧	13081600196	{}	\N	f	f	f	\N	3	安恒日审	2026-04-22	2026-04-22
\.


--
-- Data for Name: nine_a; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.nine_a (id, opportunity_id, key_events, budget, decision_chain_influence, customer_challenges, customer_needs, solution_differentiation, competitors, buying_method, close_date) FROM stdin;
\.


--
-- Data for Name: nine_a_versions; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.nine_a_versions (id, opportunity_id, version_number, key_events, budget, decision_chain_influence, customer_challenges, customer_needs, solution_differentiation, competitors, buying_method, close_date, created_at, created_by_id) FROM stdin;
\.


--
-- Data for Name: operation_logs; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.operation_logs (id, user_id, user_name, action_type, entity_type, entity_id, entity_code, entity_name, old_value, new_value, description, ip_address, created_at) FROM stdin;
1	2	张健	CREATE	customer	1	PYCRM-CUST-20260418-001	测试	null	null	创建客户: 测试	172.25.0.5	2026-04-18 03:54:19.412856
2	1	Admin User	CREATE	customer	2	PYCRM-CUST-20260418-002	测试客户	null	null	创建客户: 测试客户	172.25.0.5	2026-04-18 03:56:51.925173
3	2	张健	CREATE	lead	1	PYCRM-LEAD-20260418-001	ces	null	null	创建线索: ces	172.25.0.5	2026-04-18 06:34:59.056557
4	1	Admin User	CREATE	customer	3	PYCRM-CUST-20260418-003	测试客户公司	null	null	创建客户: 测试客户公司	172.25.0.1	2026-04-18 14:01:12.680308
5	1	Admin User	CREATE	opportunity	1	PYCRM-OPP-20260418-001	测试商机	null	null	创建商机: 测试商机	172.25.0.1	2026-04-18 14:01:33.22704
6	2	张健	CREATE	opportunity	2	PYCRM-OPP-20260418-002	hkl	null	null	创建商机: hkl	172.25.0.5	2026-04-18 14:06:51.800558
7	2	张健	CREATE	follow_up	1	\N	跟进记录#1	null	null	创建跟进记录: 线索#1	172.25.0.5	2026-04-18 14:15:20.572866
8	2	张健	UPDATE	lead	1	PYCRM-LEAD-20260418-001	ces	null	null	更新线索: ces	172.25.0.5	2026-04-18 14:15:51.695634
9	2	张健	CREATE	follow_up	2	\N	跟进记录#2	null	null	创建跟进记录: 商机#2	172.25.0.5	2026-04-18 14:18:09.052156
10	2	张健	CREATE	follow_up	3	\N	跟进记录#3	null	null	创建跟进记录: 项目#2	172.25.0.5	2026-04-18 14:18:31.287149
11	2	张健	CREATE	customer	4	PYCRM-CUST-20260418-004	测试客户	null	null	创建客户: 测试客户	172.25.0.5	2026-04-18 14:28:03.354139
12	2	张健	CREATE	channel	1	\N	测试渠道	null	null	创建渠道: 测试渠道	172.25.0.5	2026-04-18 14:31:13.61881
13	2	张健	UPDATE	lead	1	PYCRM-LEAD-20260418-001	ces	null	null	更新线索: ces	172.25.0.5	2026-04-18 14:38:43.027428
14	3	周梦琪	CREATE	customer	5	PYCRM-CUST-20260420-001	111	null	null	创建客户: 111	172.25.0.5	2026-04-20 03:10:51.412997
15	3	周梦琪	CREATE	customer	6	PYCRM-CUST-20260422-001	山东汽车制造有限公司	null	null	创建客户: 山东汽车制造有限公司	172.25.0.5	2026-04-22 01:09:02.944079
16	3	周梦琪	DELETE	customer	5	PYCRM-CUST-20260420-001	111	{"credit_code": "111111111111111112", "customer_name": "111"}	null	删除客户: 111	172.25.0.5	2026-04-22 01:09:13.31539
17	3	周梦琪	CREATE	lead	2	PYCRM-LEAD-20260422-001	日审换新	null	null	创建线索: 日审换新	172.25.0.5	2026-04-22 02:04:42.002195
18	3	周梦琪	CREATE	follow_up	4	\N	跟进记录#4	null	null	创建跟进记录: 线索#2	172.25.0.5	2026-04-22 02:10:57.650801
\.


--
-- Data for Name: opportunities; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.opportunities (id, opportunity_code, opportunity_name, terminal_customer_id, opportunity_source, product_ids, products, opportunity_stage, expected_contract_amount, expected_close_date, sales_owner_id, channel_id, vendor_registration_status, vendor_discount, loss_reason, project_id, created_at) FROM stdin;
1	PYCRM-OPP-20260418-001	测试商机	3	展会	\N	{}	初步接触	100000.00	2026-05-30	1	\N	\N	\N	\N	\N	2026-04-18
2	PYCRM-OPP-20260418-002	hkl	1	主动开发	\N	{}	需求方案	2000.00	2026-04-18	2	\N	\N	\N	\N	\N	2026-04-18
\.


--
-- Data for Name: payment_plans; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.payment_plans (id, contract_id, plan_stage, plan_amount, plan_date, actual_amount, actual_date, payment_status, notes) FROM stdin;
\.


--
-- Data for Name: product_installations; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.product_installations (id, customer_id, manufacturer, product_type, product_model, license_scale, system_version, online_date, maintenance_expiry, username, password, login_url, notes, created_at, updated_at, created_by_id) FROM stdin;
1	1	爱数	服务器	33	20T	V8	2026-04-18	2026-04-18	\N	\N	\N	\N	2026-04-18 06:34:41.911015+00	2026-04-18 06:34:41.911015+00	2
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.products (id, product_code, product_name, product_type, brand_manufacturer, is_active, notes) FROM stdin;
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.projects (id, project_code, project_name, terminal_customer_id, channel_id, source_opportunity_id, product_ids, products, business_type, project_status, sales_owner_id, downstream_contract_amount, upstream_procurement_amount, direct_project_investment, additional_investment, winning_date, acceptance_date, first_payment_date, actual_payment_amount, notes, gross_margin) FROM stdin;
1	PYCRM-PRJ-20260418-001	测试项目	3	\N	\N	{}	{}	直销	进行中	1	100000.00	\N	\N	\N	\N	\N	\N	\N	\N	\N
2	PYCRM-PRJ-20260418-002	sadad	1	\N	\N	{}	{安恒}	系统集成	进行中	2	2000.00	1000.00	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: sales_targets; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.sales_targets (id, user_id, target_type, target_year, target_period, target_amount, parent_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: terminal_customers; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.terminal_customers (id, customer_code, customer_name, credit_code, customer_industry, customer_region, customer_owner_id, channel_id, main_contact, phone, customer_status, maintenance_expiry, notes) FROM stdin;
1	PYCRM-CUST-20260418-001	测试	111111111111111111	制造	山东省/青岛市	2	\N	测试姓名	17664074259	活跃	\N	\N
2	PYCRM-CUST-20260418-002	测试客户	123456789012345678	制造	山东省/济南市	1	\N	\N	\N	活跃	\N	\N
3	PYCRM-CUST-20260418-003	测试客户公司	91370100MA3CFXXXXX	制造业	济南市	1	\N	张三	13800138001	潜在客户	\N	\N
4	PYCRM-CUST-20260418-004	测试客户	111111222222222222	化工	山东省/东营市	2	\N	测试联系人	176666666666	潜在	\N	\N
6	PYCRM-CUST-20260422-001	山东汽车制造有限公司	xxxxxxxxxxxxxxxxxx	汽车	山东省/烟台市	3	\N	于欣尧	13081600196	潜在	\N	安恒老用户（堡垒机，日审）但由于服务不好，客户满意的有问题
\.


--
-- Data for Name: unified_targets; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.unified_targets (id, target_type, channel_id, user_id, year, quarter, month, performance_target, opportunity_target, project_count_target, development_goal, achieved_performance, achieved_opportunity, achieved_project_count, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.users (id, email, hashed_password, is_active, role, name, feishu_id, phone, avatar, sales_leader_id, sales_region, sales_product_line, uuid_id, cuid_id, functional_role, responsibility_role, department, user_status, created_at, updated_at, full_name) FROM stdin;
1	admin@example.com	$2b$12$Z.BukRUiAQvFp3tjp0g4Me0m29XTg/qxrlo85RFxTcG8ot5ZM9c36	t	admin	Admin User	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	ACTIVE	2026-04-17 15:03:07.511159+00	\N	\N
4	hanliyue@purytech.cn	\N	t	sales	韩立岳	ou_a240c94fd1f906ffe5b1fb1fe0047382	+8618254135830	https://s1-imfile.feishucdn.com/static-resource/v1/v3_00105_d0e00143-6691-46f4-aa0b-c509b42f621g~?image_size=72x72&cut_type=&quality=&format=image&sticker_format=.webp	\N	\N	\N	\N	\N	\N	\N	\N	ACTIVE	2026-04-20 03:00:07.814646+00	\N	\N
2	zhangjian@purytech.cn	\N	t	admin	张健	ou_f4f87a1bf0d3f17f3d32b3bf4abdda26	+8617664074259	https://s1-imfile.feishucdn.com/static-resource/v1/v3_00o1_b97a2ae3-9eee-44aa-bfa1-10f74b82d30g~?image_size=72x72&cut_type=&quality=&format=image&sticker_format=.webp	\N	\N	\N	\N	\N	\N	\N	\N	ACTIVE	2026-04-17 15:16:45.696981+00	2026-04-20 07:55:48.075185+00	\N
3	zhoumengqi@purytech.cn	\N	t	sales	周梦琪	ou_9f773b23f09e28e2871cfaac016f423d	+8615589233201	https://s3-imfile.feishucdn.com/static-resource/v1/v3_0010h_7d1665db-9964-4aea-96f6-9bcb59a12fcg~?image_size=72x72&cut_type=&quality=&format=image&sticker_format=.webp	\N	\N	\N	\N	\N	\N	\N	\N	ACTIVE	2026-04-19 05:22:32.077712+00	2026-04-22 01:52:21.799461+00	\N
\.


--
-- Data for Name: work_order_technicians; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.work_order_technicians (id, work_order_id, technician_id, created_at) FROM stdin;
\.


--
-- Data for Name: work_orders; Type: TABLE DATA; Schema: public; Owner: crm_user
--

COPY public.work_orders (id, cuid_id, work_order_no, order_type, submitter_id, related_sales_id, customer_name, customer_contact, customer_phone, has_channel, channel_id, channel_name, channel_contact, channel_phone, manufacturer_contact, work_type, priority, description, status, estimated_start_date, estimated_start_period, estimated_end_date, estimated_end_period, accepted_at, started_at, completed_at, service_summary, cancel_reason, source_type, lead_id, opportunity_id, project_id, created_at, updated_at) FROM stdin;
\.


--
-- Name: alert_rules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.alert_rules_id_seq', 1, false);


--
-- Name: auto_numbers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.auto_numbers_id_seq', 11, true);


--
-- Name: channel_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.channel_assignments_id_seq', 1, false);


--
-- Name: channels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.channels_id_seq', 1, true);


--
-- Name: contract_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.contract_products_id_seq', 1, false);


--
-- Name: contracts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.contracts_id_seq', 1, false);


--
-- Name: customer_channel_links_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.customer_channel_links_id_seq', 1, false);


--
-- Name: dict_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.dict_items_id_seq', 162, true);


--
-- Name: dispatch_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.dispatch_records_id_seq', 1, false);


--
-- Name: evaluations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.evaluations_id_seq', 1, false);


--
-- Name: execution_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.execution_plans_id_seq', 1, false);


--
-- Name: follow_ups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.follow_ups_id_seq', 4, true);


--
-- Name: knowledge_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.knowledge_id_seq', 1, false);


--
-- Name: leads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.leads_id_seq', 2, true);


--
-- Name: nine_a_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.nine_a_id_seq', 1, false);


--
-- Name: nine_a_versions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.nine_a_versions_id_seq', 1, false);


--
-- Name: operation_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.operation_logs_id_seq', 18, true);


--
-- Name: opportunities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.opportunities_id_seq', 2, true);


--
-- Name: payment_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.payment_plans_id_seq', 1, false);


--
-- Name: product_installations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.product_installations_id_seq', 1, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.projects_id_seq', 2, true);


--
-- Name: sales_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.sales_targets_id_seq', 1, false);


--
-- Name: terminal_customers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.terminal_customers_id_seq', 6, true);


--
-- Name: unified_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.unified_targets_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: work_order_technicians_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.work_order_technicians_id_seq', 1, false);


--
-- Name: work_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crm_user
--

SELECT pg_catalog.setval('public.work_orders_id_seq', 1, false);


--
-- Name: alert_rules alert_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_pkey PRIMARY KEY (id);


--
-- Name: alert_rules alert_rules_rule_code_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.alert_rules
    ADD CONSTRAINT alert_rules_rule_code_key UNIQUE (rule_code);


--
-- Name: auto_numbers auto_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.auto_numbers
    ADD CONSTRAINT auto_numbers_pkey PRIMARY KEY (id);


--
-- Name: channel_assignments channel_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.channel_assignments
    ADD CONSTRAINT channel_assignments_pkey PRIMARY KEY (id);


--
-- Name: channels channels_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.channels
    ADD CONSTRAINT channels_pkey PRIMARY KEY (id);


--
-- Name: contract_products contract_products_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contract_products
    ADD CONSTRAINT contract_products_pkey PRIMARY KEY (id);


--
-- Name: contracts contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_pkey PRIMARY KEY (id);


--
-- Name: customer_channel_links customer_channel_links_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.customer_channel_links
    ADD CONSTRAINT customer_channel_links_pkey PRIMARY KEY (id);


--
-- Name: dict_items dict_items_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dict_items
    ADD CONSTRAINT dict_items_pkey PRIMARY KEY (id);


--
-- Name: dispatch_records dispatch_records_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records
    ADD CONSTRAINT dispatch_records_pkey PRIMARY KEY (id);


--
-- Name: dispatch_records dispatch_records_work_order_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records
    ADD CONSTRAINT dispatch_records_work_order_id_key UNIQUE (work_order_id);


--
-- Name: evaluations evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.evaluations
    ADD CONSTRAINT evaluations_pkey PRIMARY KEY (id);


--
-- Name: execution_plans execution_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.execution_plans
    ADD CONSTRAINT execution_plans_pkey PRIMARY KEY (id);


--
-- Name: follow_ups follow_ups_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups
    ADD CONSTRAINT follow_ups_pkey PRIMARY KEY (id);


--
-- Name: knowledge knowledge_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.knowledge
    ADD CONSTRAINT knowledge_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: nine_a nine_a_opportunity_id_key; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a
    ADD CONSTRAINT nine_a_opportunity_id_key UNIQUE (opportunity_id);


--
-- Name: nine_a nine_a_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a
    ADD CONSTRAINT nine_a_pkey PRIMARY KEY (id);


--
-- Name: nine_a_versions nine_a_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a_versions
    ADD CONSTRAINT nine_a_versions_pkey PRIMARY KEY (id);


--
-- Name: operation_logs operation_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.operation_logs
    ADD CONSTRAINT operation_logs_pkey PRIMARY KEY (id);


--
-- Name: opportunities opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_pkey PRIMARY KEY (id);


--
-- Name: payment_plans payment_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.payment_plans
    ADD CONSTRAINT payment_plans_pkey PRIMARY KEY (id);


--
-- Name: product_installations product_installations_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.product_installations
    ADD CONSTRAINT product_installations_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: sales_targets sales_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.sales_targets
    ADD CONSTRAINT sales_targets_pkey PRIMARY KEY (id);


--
-- Name: terminal_customers terminal_customers_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.terminal_customers
    ADD CONSTRAINT terminal_customers_pkey PRIMARY KEY (id);


--
-- Name: unified_targets unified_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.unified_targets
    ADD CONSTRAINT unified_targets_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: work_order_technicians work_order_technicians_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_pkey PRIMARY KEY (id);


--
-- Name: work_orders work_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_pkey PRIMARY KEY (id);


--
-- Name: idx_dispatch_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_dispatch_created_at ON public.dispatch_records USING btree (created_at);


--
-- Name: idx_dispatch_lead; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_dispatch_lead ON public.dispatch_records USING btree (lead_id) WHERE (lead_id IS NOT NULL);


--
-- Name: idx_dispatch_opportunity; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_dispatch_opportunity ON public.dispatch_records USING btree (opportunity_id) WHERE (opportunity_id IS NOT NULL);


--
-- Name: idx_dispatch_project; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_dispatch_project ON public.dispatch_records USING btree (project_id) WHERE (project_id IS NOT NULL);


--
-- Name: idx_dispatch_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_dispatch_status ON public.dispatch_records USING btree (status);


--
-- Name: idx_logs_action; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_logs_action ON public.operation_logs USING btree (action_type);


--
-- Name: idx_logs_entity; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_logs_entity ON public.operation_logs USING btree (entity_type, entity_id);


--
-- Name: idx_logs_time; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_logs_time ON public.operation_logs USING btree (created_at);


--
-- Name: idx_logs_user; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_logs_user ON public.operation_logs USING btree (user_id);


--
-- Name: idx_pi_customer; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_pi_customer ON public.product_installations USING btree (customer_id);


--
-- Name: idx_pi_manufacturer; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_pi_manufacturer ON public.product_installations USING btree (manufacturer);


--
-- Name: idx_pi_online_date; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX idx_pi_online_date ON public.product_installations USING btree (online_date);


--
-- Name: ix_auto_numbers_entity_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_auto_numbers_entity_type ON public.auto_numbers USING btree (entity_type);


--
-- Name: ix_auto_numbers_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_auto_numbers_id ON public.auto_numbers USING btree (id);


--
-- Name: ix_channel_assignments_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channel_assignments_channel_id ON public.channel_assignments USING btree (channel_id);


--
-- Name: ix_channel_assignments_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channel_assignments_id ON public.channel_assignments USING btree (id);


--
-- Name: ix_channel_assignments_user_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channel_assignments_user_id ON public.channel_assignments USING btree (user_id);


--
-- Name: ix_channels_business_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channels_business_type ON public.channels USING btree (business_type);


--
-- Name: ix_channels_channel_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_channels_channel_code ON public.channels USING btree (channel_code);


--
-- Name: ix_channels_channel_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channels_channel_status ON public.channels USING btree (channel_status);


--
-- Name: ix_channels_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_channels_id ON public.channels USING btree (id);


--
-- Name: ix_channels_uuid_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_channels_uuid_id ON public.channels USING btree (uuid_id);


--
-- Name: ix_contract_products_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_contract_products_id ON public.contract_products USING btree (id);


--
-- Name: ix_contracts_contract_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_contracts_contract_code ON public.contracts USING btree (contract_code);


--
-- Name: ix_contracts_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_contracts_id ON public.contracts USING btree (id);


--
-- Name: ix_customer_channel_links_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_customer_channel_links_channel_id ON public.customer_channel_links USING btree (channel_id);


--
-- Name: ix_customer_channel_links_customer_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_customer_channel_links_customer_id ON public.customer_channel_links USING btree (customer_id);


--
-- Name: ix_customer_channel_links_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_customer_channel_links_id ON public.customer_channel_links USING btree (id);


--
-- Name: ix_dict_items_dict_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_dict_items_dict_type ON public.dict_items USING btree (dict_type);


--
-- Name: ix_dict_items_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_dict_items_id ON public.dict_items USING btree (id);


--
-- Name: ix_dispatch_records_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_dispatch_records_id ON public.dispatch_records USING btree (id);


--
-- Name: ix_evaluations_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_evaluations_id ON public.evaluations USING btree (id);


--
-- Name: ix_evaluations_work_order_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_evaluations_work_order_id ON public.evaluations USING btree (work_order_id);


--
-- Name: ix_execution_plans_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_channel_id ON public.execution_plans USING btree (channel_id);


--
-- Name: ix_execution_plans_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_created_at ON public.execution_plans USING btree (created_at);


--
-- Name: ix_execution_plans_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_id ON public.execution_plans USING btree (id);


--
-- Name: ix_execution_plans_plan_period; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_plan_period ON public.execution_plans USING btree (plan_period);


--
-- Name: ix_execution_plans_plan_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_plan_type ON public.execution_plans USING btree (plan_type);


--
-- Name: ix_execution_plans_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_status ON public.execution_plans USING btree (status);


--
-- Name: ix_execution_plans_user_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_execution_plans_user_id ON public.execution_plans USING btree (user_id);


--
-- Name: ix_follow_ups_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_follow_ups_id ON public.follow_ups USING btree (id);


--
-- Name: ix_knowledge_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_knowledge_created_at ON public.knowledge USING btree (created_at);


--
-- Name: ix_knowledge_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_knowledge_id ON public.knowledge USING btree (id);


--
-- Name: ix_knowledge_problem_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_knowledge_problem_type ON public.knowledge USING btree (problem_type);


--
-- Name: ix_knowledge_title; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_knowledge_title ON public.knowledge USING btree (title);


--
-- Name: ix_leads_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_leads_id ON public.leads USING btree (id);


--
-- Name: ix_leads_lead_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_leads_lead_code ON public.leads USING btree (lead_code);


--
-- Name: ix_leads_source_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_leads_source_channel_id ON public.leads USING btree (source_channel_id);


--
-- Name: ix_nine_a_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_nine_a_id ON public.nine_a USING btree (id);


--
-- Name: ix_nine_a_versions_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_nine_a_versions_id ON public.nine_a_versions USING btree (id);


--
-- Name: ix_operation_logs_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_operation_logs_id ON public.operation_logs USING btree (id);


--
-- Name: ix_opportunities_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_opportunities_id ON public.opportunities USING btree (id);


--
-- Name: ix_opportunities_opportunity_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_opportunities_opportunity_code ON public.opportunities USING btree (opportunity_code);


--
-- Name: ix_payment_plans_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_payment_plans_id ON public.payment_plans USING btree (id);


--
-- Name: ix_product_installations_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_product_installations_id ON public.product_installations USING btree (id);


--
-- Name: ix_products_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_products_id ON public.products USING btree (id);


--
-- Name: ix_products_product_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_products_product_code ON public.products USING btree (product_code);


--
-- Name: ix_projects_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_projects_id ON public.projects USING btree (id);


--
-- Name: ix_projects_project_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_projects_project_code ON public.projects USING btree (project_code);


--
-- Name: ix_sales_targets_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_sales_targets_id ON public.sales_targets USING btree (id);


--
-- Name: ix_terminal_customers_customer_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_terminal_customers_customer_code ON public.terminal_customers USING btree (customer_code);


--
-- Name: ix_terminal_customers_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_terminal_customers_id ON public.terminal_customers USING btree (id);


--
-- Name: ix_unified_targets_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_channel_id ON public.unified_targets USING btree (channel_id);


--
-- Name: ix_unified_targets_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_created_at ON public.unified_targets USING btree (created_at);


--
-- Name: ix_unified_targets_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_id ON public.unified_targets USING btree (id);


--
-- Name: ix_unified_targets_month; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_month ON public.unified_targets USING btree (month);


--
-- Name: ix_unified_targets_quarter; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_quarter ON public.unified_targets USING btree (quarter);


--
-- Name: ix_unified_targets_target_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_target_type ON public.unified_targets USING btree (target_type);


--
-- Name: ix_unified_targets_user_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_user_id ON public.unified_targets USING btree (user_id);


--
-- Name: ix_unified_targets_year; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_unified_targets_year ON public.unified_targets USING btree (year);


--
-- Name: ix_users_cuid_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_users_cuid_id ON public.users USING btree (cuid_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_feishu_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_users_feishu_id ON public.users USING btree (feishu_id);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_uuid_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_users_uuid_id ON public.users USING btree (uuid_id);


--
-- Name: ix_work_order_technicians_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_order_technicians_id ON public.work_order_technicians USING btree (id);


--
-- Name: ix_work_order_technicians_technician_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_order_technicians_technician_id ON public.work_order_technicians USING btree (technician_id);


--
-- Name: ix_work_order_technicians_work_order_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_order_technicians_work_order_id ON public.work_order_technicians USING btree (work_order_id);


--
-- Name: ix_work_orders_channel_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_channel_id ON public.work_orders USING btree (channel_id);


--
-- Name: ix_work_orders_created_at; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_created_at ON public.work_orders USING btree (created_at);


--
-- Name: ix_work_orders_cuid_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_work_orders_cuid_id ON public.work_orders USING btree (cuid_id);


--
-- Name: ix_work_orders_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_id ON public.work_orders USING btree (id);


--
-- Name: ix_work_orders_lead_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_lead_id ON public.work_orders USING btree (lead_id);


--
-- Name: ix_work_orders_opportunity_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_opportunity_id ON public.work_orders USING btree (opportunity_id);


--
-- Name: ix_work_orders_order_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_order_type ON public.work_orders USING btree (order_type);


--
-- Name: ix_work_orders_project_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_project_id ON public.work_orders USING btree (project_id);


--
-- Name: ix_work_orders_related_sales_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_related_sales_id ON public.work_orders USING btree (related_sales_id);


--
-- Name: ix_work_orders_source_type; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_source_type ON public.work_orders USING btree (source_type);


--
-- Name: ix_work_orders_status; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_status ON public.work_orders USING btree (status);


--
-- Name: ix_work_orders_submitter_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_work_orders_submitter_id ON public.work_orders USING btree (submitter_id);


--
-- Name: ix_work_orders_work_order_no; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_work_orders_work_order_no ON public.work_orders USING btree (work_order_no);


--
-- Name: channel_assignments channel_assignments_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.channel_assignments
    ADD CONSTRAINT channel_assignments_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: contract_products contract_products_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contract_products
    ADD CONSTRAINT contract_products_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: contract_products contract_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contract_products
    ADD CONSTRAINT contract_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: contracts contracts_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: contracts contracts_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: contracts contracts_terminal_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_terminal_customer_id_fkey FOREIGN KEY (terminal_customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: customer_channel_links customer_channel_links_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.customer_channel_links
    ADD CONSTRAINT customer_channel_links_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: customer_channel_links customer_channel_links_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.customer_channel_links
    ADD CONSTRAINT customer_channel_links_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: dict_items dict_items_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dict_items
    ADD CONSTRAINT dict_items_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.dict_items(id);


--
-- Name: dispatch_records dispatch_records_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records
    ADD CONSTRAINT dispatch_records_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE SET NULL;


--
-- Name: dispatch_records dispatch_records_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records
    ADD CONSTRAINT dispatch_records_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id) ON DELETE SET NULL;


--
-- Name: dispatch_records dispatch_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.dispatch_records
    ADD CONSTRAINT dispatch_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: evaluations evaluations_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.evaluations
    ADD CONSTRAINT evaluations_work_order_id_fkey FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id);


--
-- Name: execution_plans execution_plans_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.execution_plans
    ADD CONSTRAINT execution_plans_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: follow_ups follow_ups_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups
    ADD CONSTRAINT follow_ups_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: follow_ups follow_ups_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups
    ADD CONSTRAINT follow_ups_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: follow_ups follow_ups_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups
    ADD CONSTRAINT follow_ups_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: follow_ups follow_ups_terminal_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.follow_ups
    ADD CONSTRAINT follow_ups_terminal_customer_id_fkey FOREIGN KEY (terminal_customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: leads leads_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: leads leads_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: leads leads_source_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_source_channel_id_fkey FOREIGN KEY (source_channel_id) REFERENCES public.channels(id);


--
-- Name: leads leads_terminal_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_terminal_customer_id_fkey FOREIGN KEY (terminal_customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: nine_a nine_a_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a
    ADD CONSTRAINT nine_a_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id) ON DELETE CASCADE;


--
-- Name: nine_a_versions nine_a_versions_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.nine_a_versions
    ADD CONSTRAINT nine_a_versions_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id) ON DELETE CASCADE;


--
-- Name: opportunities opportunities_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: opportunities opportunities_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: opportunities opportunities_terminal_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_terminal_customer_id_fkey FOREIGN KEY (terminal_customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: payment_plans payment_plans_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.payment_plans
    ADD CONSTRAINT payment_plans_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: product_installations product_installations_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.product_installations
    ADD CONSTRAINT product_installations_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.terminal_customers(id) ON DELETE CASCADE;


--
-- Name: projects projects_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: projects projects_source_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_source_opportunity_id_fkey FOREIGN KEY (source_opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: projects projects_terminal_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_terminal_customer_id_fkey FOREIGN KEY (terminal_customer_id) REFERENCES public.terminal_customers(id);


--
-- Name: sales_targets sales_targets_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.sales_targets
    ADD CONSTRAINT sales_targets_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.sales_targets(id);


--
-- Name: terminal_customers terminal_customers_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.terminal_customers
    ADD CONSTRAINT terminal_customers_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: unified_targets unified_targets_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.unified_targets
    ADD CONSTRAINT unified_targets_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: users users_sales_leader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_sales_leader_id_fkey FOREIGN KEY (sales_leader_id) REFERENCES public.users(id);


--
-- Name: work_order_technicians work_order_technicians_work_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_order_technicians
    ADD CONSTRAINT work_order_technicians_work_order_id_fkey FOREIGN KEY (work_order_id) REFERENCES public.work_orders(id) ON DELETE CASCADE;


--
-- Name: work_orders work_orders_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id);


--
-- Name: work_orders work_orders_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: work_orders work_orders_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: work_orders work_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- PostgreSQL database dump complete
--

\unrestrict dpBFR5pxvkp7zIOcFo6s6pVoiNscSQdhLbM4QoSUeSBV73oyxeR1B0havggjZAm

