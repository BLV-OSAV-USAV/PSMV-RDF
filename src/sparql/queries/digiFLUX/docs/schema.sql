create table dbo.alternate_id
(
    id               bigint identity
        primary key,
    value            nvarchar(50),
    source_system_id nvarchar(50)
)
go

create table dbo.api_lock_config
(
    id              bigint identity
        primary key,
    product_family  nvarchar(50),
    api_access_type nvarchar(50),
    active          bit
)
go

create table dbo.api_lock_history
(
    id              bigint identity
        primary key,
    product_family  nvarchar(50),
    api_access_type nvarchar(50),
    start           datetime2,
    finish          datetime2,
    status          nvarchar(30),
    login_id        nvarchar(30)
)
go

create table dbo.botanical_plant
(
    id             bigint identity
        primary key,
    code           nvarchar(50) not null,
    designation_de nvarchar(255),
    designation_fr nvarchar(255),
    designation_it nvarchar(255),
    designation_en nvarchar(255),
    designation_la nvarchar(255),
    explanation    nvarchar(2000)
)
go

create table dbo.bur_web_cache
(
    id              bigint identity
        primary key,
    uid_or_bur      nvarchar(20),
    name            nvarchar(255),
    updated         datetime2,
    not_found_since datetime2
)
go

create unique index IDX_bur_web_cache_uid_or_bur
    on dbo.bur_web_cache (uid_or_bur)
go

create table dbo.dressed_seed
(
    id                                         nvarchar(50) not null
        primary key,
    admission_type                             nvarchar(30),
    designation_de                             nvarchar(255),
    designation_en                             nvarchar(255),
    designation_fr                             nvarchar(255),
    designation_it                             nvarchar(255),
    transaction_unit                           nvarchar(20),
    retail_name_de                             nvarchar(255),
    retail_name_fr                             nvarchar(255),
    retail_name_it                             nvarchar(255),
    retail_name_en                             nvarchar(255),
    valid_from_inclusive                       date,
    locked                                     bit default 0,
    explanation                                nvarchar(2000),
    retail_name_explanation                    nvarchar(2000),
    designation_la                             nvarchar(255),
    retail_name_la                             nvarchar(255),
    botanical_plant_id                         bigint
        constraint FK_DRESSED_SEED_BOTANICAL_PLANT
            references dbo.botanical_plant,
    has_reporting_obligation_by_admin_override bit,
    valid_to_exclusive                         date
)
go

create table dbo.dressed_seed_alternate_id
(
    alternate_id_id bigint,
    dressed_seed_id nvarchar(50)
        constraint FK_DRESSED_SEED_ALTERNATE_ID_DRESSED_SEED
            references dbo.dressed_seed
)
go

create clustered index IDX_dressed_seed_alternate_id_dressed_seed_id
    on dbo.dressed_seed_alternate_id (dressed_seed_id)
go

create index IDX_dressed_seed_alternate_id_alternate_id_id
    on dbo.dressed_seed_alternate_id (alternate_id_id)
go

create table dbo.dressed_seed_variety
(
    dressed_seed_id nvarchar(50) not null
        constraint FK_DRESSED_SEED_VARIETY_DRESSED_SEED
            references dbo.dressed_seed,
    variety         nvarchar(50)
)
go

create clustered index IDX_dressed_seed_variety_dressed_seed_id
    on dbo.dressed_seed_variety (dressed_seed_id)
go

create table dbo.excel_import
(
    id               bigint identity
        primary key,
    product_family   nvarchar(150),
    file_name        nvarchar(255),
    file_path        nvarchar(255),
    status           nvarchar(150),
    upload_timestamp datetime2
)
go

create table dbo.excel_import_error
(
    id             bigint identity
        primary key,
    import_file_id bigint
        constraint FK_FEEDSTUFF_IMPORT_ROW_STATUS_EXCEL_IMPORT
            references dbo.excel_import,
    row_number     int,
    message        nvarchar(255),
    warning_only   bit
)
go

create table dbo.feedstuff
(
    id                                         nvarchar(50) not null
        primary key,
    designation_de                             nvarchar(255),
    designation_en                             nvarchar(255),
    designation_fr                             nvarchar(255),
    designation_it                             nvarchar(255),
    type_of_product                            nvarchar(30),
    lot_number                                 nvarchar(50),
    feedstuff_product_category                 nvarchar(20),
    manufacturer                               nvarchar(20),
    origin                                     nvarchar(20),
    organic_regulation_conformity              nvarchar(20),
    laboratory_analysis_date                   date,
    transaction_unit                           nvarchar(20),
    density                                    numeric(19, 4),
    sale_from_inclusive                        date,
    sale_to_inclusive                          date,
    version                                    bigint,
    locked                                     bit default 0,
    explanation                                nvarchar(2000),
    reference_to_product                       nvarchar(50),
    type_of_feedstuff_product                  nvarchar(50),
    designation_la                             nvarchar(255),
    manufacturer_bur                           nvarchar(20),
    ref_designation_de                         nvarchar(255),
    ref_designation_en                         nvarchar(255),
    ref_designation_fr                         nvarchar(255),
    ref_designation_it                         nvarchar(255),
    ref_designation_la                         nvarchar(255),
    ref_explanation                            nvarchar(255),
    verification_document_id                   nvarchar(255),
    has_reporting_obligation_by_admin_override bit,
    imported                                   bit,
    admission_url                              nvarchar(255),
    used_for_import                            bit default 0,
    valid_from_inclusive                       date,
    valid_to_exclusive                         date,
    supersedes_id                              nvarchar(50)
        constraint fk_supersedes_id
            references dbo.feedstuff,
    is_empty_template                          bit
        constraint df_feedstuff_is_empty_template default 0 not null
)
go

create index idx_feedstuff_supersedes_id
    on dbo.feedstuff (supersedes_id)
go

create table dbo.feedstuff_alternate_id
(
    alternate_id_id bigint,
    feedstuff_id    nvarchar(50)
        constraint FK_FEEDSTUFF_ALTERNATE_ID_FEEDSTUFF
            references dbo.feedstuff
)
go

create clustered index IDX_feedstuff_alternate_id_feedstuff_id
    on dbo.feedstuff_alternate_id (feedstuff_id)
go

create index IDX_feedstuff_alternate_id_alternate_id_id
    on dbo.feedstuff_alternate_id (alternate_id_id)
go

create table dbo.feedstuff_intended_for_animal
(
    feedstuff_id        nvarchar(50) not null
        constraint FK_FEEDSTUFF_INTENDED_FOR_ANIMAL_FEEDSTUFF
            references dbo.feedstuff,
    intended_for_animal nvarchar(50)
)
go

create clustered index IDX_feedstuff_intended_for_animal_feedstuff_id
    on dbo.feedstuff_intended_for_animal (feedstuff_id)
go

create table dbo.feedstuff_label
(
    feedstuff_id nvarchar(50) not null
        constraint FK_FEEDSTUFF_LABEL_FEEDSTUFF
            references dbo.feedstuff,
    label        nvarchar(50)
)
go

create clustered index IDX_feedstuff_label_feedstuff_id
    on dbo.feedstuff_label (feedstuff_id)
go

create table dbo.feedstuff_verification_document_id
(
    feedstuff_id             nvarchar(50) not null
        constraint FK_FEEDSTUFF_VERIFICATION_DOCUMENT_ID_FEEDSTUFF
            references dbo.feedstuff,
    verification_document_id nvarchar(255)
)
go

create clustered index IDX_feedstuff_verification_document_id_feedstuff_id
    on dbo.feedstuff_verification_document_id (feedstuff_id)
go

create table dbo.fertiliser_product
(
    id                                         nvarchar(50) not null
        constraint pk_fertiliser_product
            primary key,
    designation_de                             nvarchar(255),
    designation_fr                             nvarchar(255),
    designation_it                             nvarchar(255),
    designation_en                             nvarchar(255),
    fertiliser_product_category                nvarchar(50),
    manufacturer_uid                           nvarchar(20),
    transaction_unit                           nvarchar(20),
    sale_from_inclusive                        date,
    sale_to_inclusive                          date,
    version                                    bigint,
    density                                    numeric(19, 4),
    locked                                     bit default 0,
    explanation                                nvarchar(2000),
    manufacturer_vn                            bigint,
    manufacturer_eiam                          nvarchar(50),
    manufacturer_uuid                          nvarchar(50),
    manufacturer_email                         nvarchar(100),
    designation_la                             nvarchar(255),
    has_reporting_obligation_by_admin_override bit,
    valid_from_inclusive                       date,
    valid_to_exclusive                         date,
    supersedes_id                              nvarchar(50)
        constraint fk_fertiliser_product_supersedes_id
            references dbo.fertiliser_product
)
go

create table dbo.fertiliser_alternate_id
(
    alternate_id_id       bigint
        constraint FK_FERTILISER_ALTERNATE_ID_ALTERNATE_ID
            references dbo.alternate_id,
    fertiliser_product_id nvarchar(50)
        constraint FK_FERTILISER_ALTERNATE_ID_FERTILISER
            references dbo.fertiliser_product
)
go

create clustered index IDX_fertiliser_alternate_id_fertiliser_product_id
    on dbo.fertiliser_alternate_id (fertiliser_product_id)
go

create index IDX_fertiliser_alternate_id_alternate_id_id
    on dbo.fertiliser_alternate_id (alternate_id_id)
go

create index idx_fertiliser_product_supersedes_id
    on dbo.fertiliser_product (supersedes_id)
go

create table dbo.flyway_schema_history
(
    installed_rank int                        not null
        constraint flyway_schema_history_pk
            primary key,
    version        nvarchar(50),
    description    nvarchar(200),
    type           nvarchar(20)               not null,
    script         nvarchar(1000)             not null,
    checksum       int,
    installed_by   nvarchar(100)              not null,
    installed_on   datetime default getdate() not null,
    execution_time int                        not null,
    success        bit                        not null
)
go

create index flyway_schema_history_s_idx
    on dbo.flyway_schema_history (success)
go

create table dbo.gtin_range
(
    id              bigint identity
        primary key,
    start_inclusive int           not null,
    end_inclusive   int           not null,
    name            nvarchar(255) not null,
    response        nvarchar(10)  not null
)
go

create table dbo.hazard_label
(
    id             bigint identity
        primary key,
    code           nvarchar(50),
    designation_de nvarchar(255),
    designation_en nvarchar(255),
    designation_fr nvarchar(255),
    designation_it nvarchar(255),
    explanation    nvarchar(2000),
    designation_la nvarchar(255)
)
go

create table dbo.import_job_history
(
    id               bigint identity
        primary key,
    source_system_id nvarchar(20) not null,
    start            datetime2,
    finish           datetime2,
    count            bigint,
    status           nvarchar(30)
)
go

create table dbo.indication
(
    id                                  bigint identity
        primary key,
    admission_type                      nvarchar(30),
    dosage_from                         numeric(19, 6),
    dosage_to                           numeric(19, 6),
    emergency_admission_end_inclusive   date,
    emergency_admission_start_inclusive date,
    unit                                nvarchar(20),
    waiting_period                      int,
    source_system_id                    nvarchar(20)
)
go

create table dbo.indication_botanical_plant
(
    indication_id      bigint not null
        constraint FK_INDICATION_BOTANICAL_PLANT_INDICATION
            references dbo.indication,
    botanical_plant_id bigint
        constraint FK_INDICATION_BOTANICAL_PLANT
            references dbo.botanical_plant
)
go

create clustered index IDX_indication_botanical_plant_indication_id
    on dbo.indication_botanical_plant (indication_id)
go

create index IDX_indication_botanical_plant_botanical_plant_id
    on dbo.indication_botanical_plant (botanical_plant_id)
go

create table dbo.inventory_access_cache
(
    id                bigint identity
        primary key,
    inventory_id      nvarchar(36),
    access_permission smallint,
    login_id          nvarchar(10),
    bur               nvarchar(20),
    uid               nvarchar(20),
    product_id        nvarchar(50)
)
go

create index IDX_inventory_access_cache_login_id_access_permission
    on dbo.inventory_access_cache (login_id, access_permission, bur, uid) include (inventory_id, product_id)
go

create index IDX_inventory_access_cache_uid_bur_access_permission
    on dbo.inventory_access_cache (uid, bur, access_permission) include (login_id)
go

create index IDX_inventory_access_cache_role
    on dbo.inventory_access_cache (access_permission)
go

create index IDX_inventory_access_cache_product_id_access_permission
    on dbo.inventory_access_cache (product_id, access_permission, login_id)
go

create table dbo.job_lock
(
    job_type  varchar(10)                          not null,
    owner_key int                                  not null,
    locked_at datetime2(6)                         not null,
    lock_key  nvarchar(20)
        constraint DF_job_lock_lock_key default '' not null,
    constraint PK__JobLock_ID
        primary key (job_type, lock_key)
)
go

create table dbo.mail_address
(
    id                     bigint identity
        primary key,
    organisation_name      nvarchar(60),
    address_line1          nvarchar(150),
    address_line2          nvarchar(150),
    street                 nvarchar(150),
    house_number           nvarchar(30),
    post_office_box_number bigint,
    town                   nvarchar(40),
    swiss_zip_code         bigint,
    swiss_zip_code_add_on  nvarchar(2),
    foreign_zip_code       nvarchar(15),
    country_id_iso2        nvarchar(2),
    country_name_short     nvarchar(50)
)
go

create table dbo.manure_derivation
(
    id                    bigint identity
        primary key,
    source_id             nvarchar(50),
    source_system_id      nvarchar(50),
    npr_code              nvarchar(50),
    housing               nvarchar(50),
    percentage_allocation numeric(5, 2)
)
go

create table dbo.manure_derivation_utilisation
(
    manure_derivation_id bigint not null
        constraint FK_MANURE_DERIVATION_UTILISATION_MANURE_DERIVATION
            references dbo.manure_derivation,
    utilisation          nvarchar(20)
)
go

create clustered index IDX_manure_derivation_utilisation_manure_derivation_id
    on dbo.manure_derivation_utilisation (manure_derivation_id)
go

create table dbo.manure_recycling_product
(
    id                                         nvarchar(50)                not null
        primary key,
    density                                    numeric(19, 4),
    designation_de                             nvarchar(255),
    designation_en                             nvarchar(255),
    designation_fr                             nvarchar(255),
    designation_it                             nvarchar(255),
    laboratory_analysis_date                   date,
    manufacturer                               nvarchar(20),
    manure_recycling_product_category          nvarchar(20),
    matter_state                               nvarchar(20),
    transaction_unit                           nvarchar(20),
    type_of_manure_recycling_product           nvarchar(100),
    valid_from_inclusive                       date,
    verification_document_id                   nvarchar(255),
    version                                    bigint,
    type_of_product                            nvarchar(30),
    locked                                     bit default 0,
    explanation                                nvarchar(2000),
    reference_to_product                       nvarchar(50),
    designation_la                             nvarchar(255),
    manufacturer_uid                           nvarchar(20),
    ref_designation_de                         nvarchar(255),
    ref_designation_en                         nvarchar(255),
    ref_designation_fr                         nvarchar(255),
    ref_designation_it                         nvarchar(255),
    ref_designation_la                         nvarchar(255),
    ref_explanation                            nvarchar(255),
    has_reporting_obligation_by_admin_override bit,
    hoduflu_nutrient_balance_form              nvarchar(255),
    hoduflu_nutrient_balance_category          nvarchar(255),
    valid_to_exclusive                         date,
    supersedes_id                              nvarchar(50)
        constraint fk_manure_recycling_product_supersedes_id
            references dbo.manure_recycling_product,
    is_empty_template                          bit
        constraint df_manure_recycling_product_is_empty_template default 0 not null,
    facultative_text                           nvarchar(255)
)
go

create index idx_manure_recycling_product_supersedes_id
    on dbo.manure_recycling_product (supersedes_id)
go

create index idx_manure_recycling_product_type_id_valid_from_valid_to
    on dbo.manure_recycling_product (type_of_product, id, valid_from_inclusive, valid_to_exclusive)
go

create index idx_manure_recycling_product_valid_from_type_valid_to
    on dbo.manure_recycling_product (valid_from_inclusive, type_of_product, valid_to_exclusive)
go

create index idx_manure_recycling_product_type_valid_from_valid_to
    on dbo.manure_recycling_product (type_of_product, valid_from_inclusive, valid_to_exclusive)
go

create table dbo.manure_recycling_product_alternate_id
(
    alternate_id_id             bigint,
    manure_recycling_product_id nvarchar(50)
        constraint FK_MANURE_RECYCLING_PRODUCT_ALTERNATE_ID_MANURE_RECYCLING_PRODUCT
            references dbo.manure_recycling_product
)
go

create clustered index IDX_manure_recycling_product_alternate_id_manure_recycling_product_id
    on dbo.manure_recycling_product_alternate_id (manure_recycling_product_id)
go

create index IDX_manure_recycling_product_alternate_id_alternate_id_id
    on dbo.manure_recycling_product_alternate_id (alternate_id_id)
go

create table dbo.manure_recycling_product_manure_derivation
(
    manure_recycling_product_id nvarchar(50) not null
        constraint FK_MANURE_RECYCLING_PRODUCT_MANURE_DERIVATION_MANURE_RECYCLING_PRODUCT
            references dbo.manure_recycling_product,
    manure_derivation_id        bigint       not null
        constraint FK_MANURE_RECYCLING_PRODUCT_MANURE_DERIVATION_MANURE_DERIVATION
            references dbo.manure_derivation
)
go

create clustered index IDX_manure_recycling_product_manure_derivation_manure_recycling_product_id
    on dbo.manure_recycling_product_manure_derivation (manure_recycling_product_id)
go

create index IDX_manure_recycling_product_manure_derivation_manure_derivation_id
    on dbo.manure_recycling_product_manure_derivation (manure_derivation_id)
go

create table dbo.manure_recycling_product_verification_document_id
(
    manure_recycling_product_id nvarchar(50)                                                  not null
        constraint FK_MANURE_RECYCLING_PRODUCT_VERIFICATION_DOCUMENT_ID_MANURE_RECYCLING_PRODUCT
            references dbo.manure_recycling_product,
    verification_document_id    nvarchar(255),
    placeholder                 bit
        constraint df_manure_recycling_product_verification_document_id_placeholder default 0 not null
)
go

create clustered index IDX_manure_recycling_product_verification_document_id_manure_recycling_product_id
    on dbo.manure_recycling_product_verification_document_id (manure_recycling_product_id)
go

create table dbo.owner_history
(
    id               bigint identity
        primary key,
    bur              nvarchar(50) not null,
    uid              nvarchar(20),
    date_of_transfer date         not null,
    active           bit          not null
)
go

create table dbo.hofrec_owner_history
(
    manure_recycling_product_id nvarchar(50) not null,
    hofrec_owner_history_id     bigint       not null
        constraint FK_HOFREC_OWNER_HISTORY
            references dbo.owner_history,
    constraint PK_HOFREC_OWNER_HISTORY
        primary key (manure_recycling_product_id, hofrec_owner_history_id)
)
go

create table dbo.pathogen
(
    id               bigint identity
        primary key,
    source_system_id nvarchar(20),
    code             nvarchar(50),
    eppo_code        nvarchar(10),
    designation_de   nvarchar(255),
    designation_fr   nvarchar(255),
    designation_it   nvarchar(255),
    designation_en   nvarchar(255),
    designation_la   nvarchar(255),
    explanation      nvarchar(2000)
)
go

create table dbo.indication_pathogen
(
    indication_id bigint not null
        constraint FK_INDICATION_PATHOGEN_INDICATION
            references dbo.indication,
    pathogen_id   bigint
        constraint FK_INDICATION_PATHOGEN_PATHOGEN
            references dbo.pathogen
)
go

create clustered index IDX_indication_pathogen_indication_id
    on dbo.indication_pathogen (indication_id)
go

create index IDX_indication_pathogen_pathogen_id
    on dbo.indication_pathogen (pathogen_id)
go

create table dbo.plant_protection_product
(
    id                                         nvarchar(50) not null
        primary key,
    admission_url                              nvarchar(255),
    approval_date                              date,
    designation_de                             nvarchar(255),
    designation_en                             nvarchar(255),
    designation_fr                             nvarchar(255),
    designation_it                             nvarchar(255),
    exhaustion_deadline                        date,
    permission_holder                          nvarchar(20),
    sold_out_deadline                          date,
    transaction_unit                           nvarchar(20),
    version                                    bigint,
    permission_holder_address_id               bigint
        constraint FK_PLANT_PROTECTION_PRODUCT_MAIL_ADDRESS
            references dbo.mail_address,
    valid_from_inclusive                       date,
    locked                                     bit default 0,
    usage_category                             nvarchar(30),
    explanation                                nvarchar(2000),
    designation_la                             nvarchar(255),
    has_reporting_obligation_by_usage_category bit,
    has_reporting_obligation_by_admin_override bit,
    valid_to_exclusive                         date,
    supersedes_id                              nvarchar(50)
        constraint fk_plant_protection_product_supersedes_id
            references dbo.plant_protection_product
)
go

create index idx_plant_protection_product_supersedes_id
    on dbo.plant_protection_product (supersedes_id)
go

create table dbo.plant_protection_product_alternate_id
(
    alternate_id_id             bigint
        constraint FK_PLANT_PROTECTION_PRODUCT_ALTERNATE_ID_ALTERNATE_ID
            references dbo.alternate_id,
    plant_protection_product_id nvarchar(50)
        constraint FK_PLANT_PROTECTION_PRODUCT_ALTERNATE_ID_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product
)
go

create clustered index IDX_plant_protection_product_alternate_id_plant_protection_product_id
    on dbo.plant_protection_product_alternate_id (plant_protection_product_id)
go

create index IDX_plant_protection_product_alternate_id_alternate_id_id
    on dbo.plant_protection_product_alternate_id (alternate_id_id)
go

create table dbo.plant_protection_product_category
(
    id               bigint identity
        primary key,
    source_system_id nvarchar(20),
    code             nvarchar(50),
    designation_de   nvarchar(255),
    designation_fr   nvarchar(255),
    designation_it   nvarchar(255),
    designation_en   nvarchar(255),
    designation_la   nvarchar(255),
    explanation      nvarchar(2000)
)
go

create table dbo.plant_protection_product_culture
(
    id                   nvarchar(50) not null
        primary key,
    source_system_id     nvarchar(20),
    designation_de       nvarchar(255),
    designation_en       nvarchar(255),
    designation_fr       nvarchar(255),
    designation_it       nvarchar(255),
    designation_la       nvarchar(255),
    explanation          nvarchar(2000),
    eppo_code            nvarchar(50),
    valid_from_inclusive date,
    valid_to_exclusive   date
)
go

create table dbo.indication_plant_protection_product_culture
(
    indication_id                       bigint       not null
        constraint FK_INDICATION_PLANT_PROTECTION_PRODUCT_CULTURE_INDICATION
            references dbo.indication,
    plant_protection_product_culture_id nvarchar(50) not null
        constraint FK_INDICATION_PLANT_PROTECTION_PRODUCT_CULTURE_CULTURE
            references dbo.plant_protection_product_culture,
    primary key (indication_id, plant_protection_product_culture_id)
)
go

create table dbo.plant_protection_product_hazard_label
(
    plant_protection_product_id nvarchar(50) not null
        constraint FK_PLANT_PROTECTION_PRODUCT_HAZARD_LABEL_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product,
    hazard_label_id             bigint       not null
        constraint FK_PLANT_PROTECTION_PRODUCT_HAZARD_LABEL_HAZARD_LABEL
            references dbo.hazard_label,
    primary key (plant_protection_product_id, hazard_label_id)
)
go

create table dbo.plant_protection_product_indication
(
    plant_protection_product_id nvarchar(50) not null
        constraint FK_PLANT_PROTECTION_PRODUCT_INDICATION_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product,
    indication_id               bigint       not null
        constraint FK_PLANT_PROTECTION_PRODUCT_INDICATION_INDICATION
            references dbo.indication,
    primary key (plant_protection_product_id, indication_id)
)
go

create table dbo.plant_protection_product_plant_protection_product_category
(
    plant_protection_product_id          nvarchar(50) not null
        constraint FK_PLANT_PROTECTION_PRODUCT_PLANT_PROTECTION_PRODUCT_CATEGORY_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product,
    plant_protection_product_category_id bigint
        constraint FK_PLANT_PROTECTION_PRODUCT_PLANT_PROTECTION_PRODUCT_CATEGORY_CATEGORY
            references dbo.plant_protection_product_category
)
go

create clustered index IDX_plant_protection_product_category_plant_protection_product_id
    on dbo.plant_protection_product_plant_protection_product_category (plant_protection_product_id)
go

create index IDX_plant_protection_product_category_plant_protection_product_category_id
    on dbo.plant_protection_product_plant_protection_product_category (plant_protection_product_category_id)
go

create table dbo.retail_product
(
    id                   nvarchar(50) not null
        primary key,
    designation_de       nvarchar(255),
    designation_en       nvarchar(255),
    designation_fr       nvarchar(255),
    designation_it       nvarchar(255),
    designation_la       nvarchar(255),
    explanation          nvarchar(2000),
    manufacturer         nvarchar(20),
    valid_from_inclusive date,
    version              bigint,
    gtin_valid           bit,
    component_category   nvarchar(50),
    valid_to_exclusive   date,
    supersedes_id        nvarchar(50)
        constraint fk_retail_product_supersedes_id
            references dbo.retail_product
)
go

create index idx_retail_product_supersedes_id
    on dbo.retail_product (supersedes_id)
go

create table dbo.retail_product_alternate_id
(
    alternate_id_id   bigint,
    retail_product_id nvarchar(50)
)
go

create clustered index IDX_retail_product_alternate_id_retail_product_id
    on dbo.retail_product_alternate_id (retail_product_id)
go

create index IDX_retail_product_alternate_id_alternate_id_id
    on dbo.retail_product_alternate_id (alternate_id_id)
go

create table dbo.retail_product_component
(
    id                          bigint identity
        primary key,
    plant_protection_product_id nvarchar(50)
        constraint FK_RETAIL_PRODUCT_COMPONENT_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product,
    fertiliser_product_id       nvarchar(50)
        constraint FK_RETAIL_PRODUCT_COMPONENT_FERTILISER_PRODUCT
            references dbo.fertiliser_product,
    quantity                    numeric(19, 6),
    unit                        nvarchar(20)
)
go

create table dbo.retail_product_retail_product_component
(
    retail_product_id           nvarchar(50) not null
        constraint FK_RETAIL_PRODUCT
            references dbo.retail_product,
    retail_product_component_id bigint       not null
        unique
        constraint FK_RETAIL_PRODUCT_COMPONENT
            references dbo.retail_product_component,
    primary key (retail_product_id, retail_product_component_id)
)
go

create table dbo.seed_treatment
(
    id                               bigint identity
        primary key,
    quantity                         numeric(19, 4),
    unit                             nvarchar(20),
    used_plant_protection_product_id nvarchar(50)
        constraint FK_SEED_TREATMENT_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product
)
go

create table dbo.dressed_seed_seed_treatment
(
    dressed_seed_id   nvarchar(50) not null
        constraint FK_DRESSED_SEED_SEED_TREATMENT_DRESSED_SEED
            references dbo.dressed_seed,
    seed_treatment_id bigint       not null
        constraint UK_DRESSED_SEED_SEED_TREATMENT_SEED_TREATMENT
            unique
        constraint FK_DRESSED_SEED_SEED_TREATMENT_SEED_TREATMENT
            references dbo.seed_treatment,
    primary key (dressed_seed_id, seed_treatment_id)
)
go

create table dbo.substance
(
    id                                                    nvarchar(50) not null
        primary key,
    active_substance_category                             nvarchar(50),
    cross_resistance_pattern                              nvarchar(50),
    designation_de                                        nvarchar(255),
    designation_en                                        nvarchar(255),
    designation_fr                                        nvarchar(255),
    designation_it                                        nvarchar(255),
    molecular_formula                                     nvarchar(50),
    locked                                                bit default 0,
    explanation                                           nvarchar(2000),
    designation_la                                        nvarchar(255),
    has_reporting_obligation_by_active_substance_category bit,
    has_reporting_obligation_by_molecular_formula         bit
)
go

create table dbo.ingredient
(
    id                bigint identity
        primary key,
    concentration     numeric(19, 4),
    designation_de    nvarchar(255),
    designation_en    nvarchar(255),
    designation_fr    nvarchar(255),
    designation_it    nvarchar(255),
    max               numeric(19, 4),
    min               numeric(19, 4),
    quantity          numeric(19, 6),
    unit              nvarchar(20),
    substance_id      nvarchar(50) not null
        constraint FK_INGREDIENT_SUBSTANCE
            references dbo.substance,
    density           numeric(19, 4),
    explanation       nvarchar(2000),
    facility_specific bit,
    required          bit,
    designation_la    nvarchar(255),
    quantity2         numeric(19, 4),
    unit2             nvarchar(20),
    min2              numeric(19, 4),
    max2              numeric(19, 4)
)
go

create table dbo.dressed_seed_ingredient
(
    dressed_seed_id nvarchar(50) not null
        constraint FK_DRESSED_SEED_INGREDIENT_DRESSED_SEED
            references dbo.dressed_seed,
    ingredient_id   bigint       not null
        constraint UK_DRESSED_SEED_INGREDIENT_INGREDIENT
            unique
        constraint FK_DRESSED_SEED_INGREDIENT_INGREDIENT
            references dbo.ingredient,
    primary key (dressed_seed_id, ingredient_id)
)
go

create table dbo.feedstuff_ingredient
(
    feedstuff_id nvarchar(50) not null
        constraint FK_FEEDSTUFF_NUTRIENT_FEEDSTUFF
            references dbo.feedstuff,
    nutrient_id  bigint       not null
        constraint FK_FEEDSTUFF_NUTRIENT_INGREDIENT
            references dbo.ingredient,
    primary key (feedstuff_id, nutrient_id)
)
go

create table dbo.fertiliser_product_ingredient
(
    fertiliser_product_id nvarchar(50) not null
        constraint FK_FERTILISER_PRODUCT_INGREDIENT_FERTILISER_PRODUCT
            references dbo.fertiliser_product,
    ingredient_id         bigint       not null
        constraint FK_FERTILISER_PRODUCT_INGREDIENT_INGREDIENT
            references dbo.ingredient,
    primary key (fertiliser_product_id, ingredient_id)
)
go

create table dbo.manure_recycling_product_ingredient
(
    manure_recycling_product_id nvarchar(50) not null
        constraint FK_MANURE_RECYCLING_PRODUCT_INGREDIENT_MANURE_RECYCLING_PRODUCT
            references dbo.manure_recycling_product,
    ingredient_id               bigint       not null
        constraint FK_MANURE_RECYCLING_PRODUCT_INGREDIENT_INGREDIENT
            references dbo.ingredient,
    primary key (manure_recycling_product_id, ingredient_id)
)
go

create table dbo.plant_protection_product_ingredient
(
    plant_protection_product_id nvarchar(50) not null
        constraint FK_PLANT_PROTECTION_PRODUCT_INGREDIENT_PLANT_PROTECTION_PRODUCT
            references dbo.plant_protection_product,
    ingredient_id               bigint       not null
        constraint FK_PLANT_PROTECTION_PRODUCT_INGREDIENT_INGREDIENT
            references dbo.ingredient,
    primary key (plant_protection_product_id, ingredient_id)
)
go

create table dbo.substance_allowed_for
(
    substance_id nvarchar(50) not null
        constraint FK_SUBSTANCE_ALLOWED_FOR_SUBSTANCE
            references dbo.substance,
    allowed_for  nvarchar(50)
)
go

create clustered index IDX_substance_allowed_for_substance_id
    on dbo.substance_allowed_for (substance_id)
go

create table dbo.substance_allowed_units
(
    substance_id  nvarchar(50) not null
        constraint FK_SUBSTANCE_ALLOWED_UNITS_SUBSTANCE
            references dbo.substance,
    allowed_units nvarchar(20)
)
go

create clustered index IDX_substance_allowed_units_substance_id
    on dbo.substance_allowed_units (substance_id)
go

create table dbo.substance_alternate_id
(
    alternate_id_id bigint
        constraint FK_SUBSTANCE_ALTERNATE_ID_ALTERNATE_ID
            references dbo.alternate_id,
    substance_id    nvarchar(50)
        constraint FK_SUBSTANCE_ALTERNATE_ID_SUBSTANCE
            references dbo.substance
)
go

create clustered index IDX_substance_alternate_id_substance_id
    on dbo.substance_alternate_id (substance_id)
go

create index IDX_substance_alternate_id_alternate_id_id
    on dbo.substance_alternate_id (alternate_id_id)
go

create table dbo.xml_import
(
    id                        bigint identity
        primary key,
    active_substance_category nvarchar(150),
    file_name                 nvarchar(255),
    file_path                 nvarchar(255),
    status                    nvarchar(150),
    upload_timestamp          datetime2
)
go

create table dbo.xml_import_error
(
    id             bigint identity
        primary key,
    import_file_id bigint
        constraint FK_SUBSTANCE_COMPLEMENT_IMPORT_ROW_STATUS_XML_IMPORT
            references dbo.xml_import,
    row_number     int,
    message        nvarchar(max)
)
go

create table dbo.zoological_animal
(
    id                       bigint identity
        primary key,
    code                     nvarchar(50)                                  not null,
    designation_de           nvarchar(255),
    designation_fr           nvarchar(255),
    designation_it           nvarchar(255),
    designation_en           nvarchar(255),
    designation_la           nvarchar(255),
    explanation              nvarchar(2000),
    manurerecycling_relevant bit
        constraint df_zoological_animal_manurerecycling_relevant default 0 not null
)
go
