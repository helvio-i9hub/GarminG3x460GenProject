--
-- PostgreSQL database dump
--

\restrict ThA7LdKaBPyASyfOsTZI1yELK3enNLhYWYk8QVJqEtFub3vdQAqFIYpJJLgO2z5

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ais_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ais_messages (
    id integer NOT NULL,
    raw_id integer,
    message_type integer,
    mmsi integer,
    latitude double precision,
    longitude double precision,
    sog double precision,
    cog double precision,
    heading integer,
    nav_status integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw jsonb
);


ALTER TABLE public.ais_messages OWNER TO postgres;

--
-- Name: ais_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ais_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ais_messages_id_seq OWNER TO postgres;

--
-- Name: ais_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ais_messages_id_seq OWNED BY public.ais_messages.id;


--
-- Name: data_source_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.data_source_config (
    id integer NOT NULL,
    source_type character varying(10) NOT NULL,
    tcp_host character varying(100),
    tcp_port integer,
    serial_port character varying(100),
    baudrate integer DEFAULT 4800,
    enabled boolean DEFAULT true,
    CONSTRAINT data_source_config_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['TCP'::character varying, 'SERIAL'::character varying])::text[])))
);


ALTER TABLE public.data_source_config OWNER TO postgres;

--
-- Name: data_source_config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.data_source_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.data_source_config_id_seq OWNER TO postgres;

--
-- Name: data_source_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.data_source_config_id_seq OWNED BY public.data_source_config.id;


--
-- Name: nmea_parsed; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nmea_parsed (
    id integer NOT NULL,
    raw_id integer,
    talker character varying(10),
    sentence_type character varying(10),
    fields jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    latitude double precision,
    longitude double precision,
    altitude double precision,
    fix_quality integer,
    satellites integer,
    hdop double precision,
    gps_time time without time zone
);


ALTER TABLE public.nmea_parsed OWNER TO postgres;

--
-- Name: nmea_parsed_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nmea_parsed_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nmea_parsed_id_seq OWNER TO postgres;

--
-- Name: nmea_parsed_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nmea_parsed_id_seq OWNED BY public.nmea_parsed.id;


--
-- Name: nmea_raw; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nmea_raw (
    id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sentence text NOT NULL
);


ALTER TABLE public.nmea_raw OWNER TO postgres;

--
-- Name: nmea_raw_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nmea_raw_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nmea_raw_id_seq OWNER TO postgres;

--
-- Name: nmea_raw_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nmea_raw_id_seq OWNED BY public.nmea_raw.id;


--
-- Name: ais_messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ais_messages ALTER COLUMN id SET DEFAULT nextval('public.ais_messages_id_seq'::regclass);


--
-- Name: data_source_config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.data_source_config ALTER COLUMN id SET DEFAULT nextval('public.data_source_config_id_seq'::regclass);


--
-- Name: nmea_parsed id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nmea_parsed ALTER COLUMN id SET DEFAULT nextval('public.nmea_parsed_id_seq'::regclass);


--
-- Name: nmea_raw id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nmea_raw ALTER COLUMN id SET DEFAULT nextval('public.nmea_raw_id_seq'::regclass);


--
-- Name: ais_messages ais_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ais_messages
    ADD CONSTRAINT ais_messages_pkey PRIMARY KEY (id);


--
-- Name: data_source_config data_source_config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.data_source_config
    ADD CONSTRAINT data_source_config_pkey PRIMARY KEY (id);


--
-- Name: nmea_parsed nmea_parsed_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nmea_parsed
    ADD CONSTRAINT nmea_parsed_pkey PRIMARY KEY (id);


--
-- Name: nmea_raw nmea_raw_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nmea_raw
    ADD CONSTRAINT nmea_raw_pkey PRIMARY KEY (id);


--
-- Name: idx_ais_mmsi; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ais_mmsi ON public.ais_messages USING btree (mmsi);


--
-- Name: idx_nmea_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_nmea_type ON public.nmea_parsed USING btree (sentence_type);


--
-- Name: ais_messages ais_messages_raw_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ais_messages
    ADD CONSTRAINT ais_messages_raw_id_fkey FOREIGN KEY (raw_id) REFERENCES public.nmea_raw(id);


--
-- Name: nmea_parsed nmea_parsed_raw_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nmea_parsed
    ADD CONSTRAINT nmea_parsed_raw_id_fkey FOREIGN KEY (raw_id) REFERENCES public.nmea_raw(id);


--
-- PostgreSQL database dump complete
--

\unrestrict ThA7LdKaBPyASyfOsTZI1yELK3enNLhYWYk8QVJqEtFub3vdQAqFIYpJJLgO2z5

