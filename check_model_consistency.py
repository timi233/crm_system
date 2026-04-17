import psycopg2
from sqlalchemy import create_engine, MetaData, inspect
import re

DB_CONFIG = {
    "dbname": "crm_db",
    "user": "crm_admin", 
    "password": "crm_secure_pw_2024",
    "host": "localhost",
    "port": 5432
}

# Define model field definitions based on the actual model files we examined earlier
MODELS_EXPECTED = {
    'channel_assignments': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),  # Primary Key identity column
            ('user_id', 'INTEGER', False, None),
            ('channel_id', 'INTEGER', False, None),
            ('permission_level', 'VARCHAR', False, None),  # VARCHAR since it's enum in db
            ('assigned_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('assigned_by', 'INTEGER', True, None),
            ('target_responsibility', 'BOOLEAN', False, 'false'),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('updated_at', 'TIMESTAMPTZ', True, None)
        ],
        'indexes': [
            'ix_channel_assignments_user_id',
            'ix_channel_assignments_channel_id'
        ],
        'fks': [
            'channel_assignments_user_id_fkey',
            'channel_assignments_channel_id_fkey', 
            'channel_assignments_assigned_by_fkey'
        ]
    },
    'unified_targets': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),
            ('target_type', 'VARCHAR', False, None),
            ('channel_id', 'INTEGER', True, None),
            ('user_id', 'INTEGER', True, None),
            ('year', 'INTEGER', False, None),
            ('quarter', 'INTEGER', True, None),
            ('month', 'INTEGER', True, None),
            ('performance_target', 'NUMERIC', True, None),
            ('opportunity_target', 'NUMERIC', True, None),
            ('project_count_target', 'INTEGER', True, None),
            ('development_goal', 'TEXT', True, None),
            ('achieved_performance', 'NUMERIC', True, '0'),
            ('achieved_opportunity', 'NUMERIC', True, '0'),
            ('achieved_project_count', 'INTEGER', True, '0'),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('updated_at', 'TIMESTAMPTZ', True, None),
            ('created_by', 'INTEGER', True, None)
        ],
        'indexes': [
            'ix_unified_targets_target_type',
            'ix_unified_targets_channel_id', 
            'ix_unified_targets_user_id',
            'ix_unified_targets_year',
            'ix_unified_targets_quarter'
        ],
        'fks': [
            'unified_targets_channel_id_fkey',
            'unified_targets_user_id_fkey',
            'unified_targets_created_by_fkey'
        ]
    },
    'execution_plans': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),
            ('channel_id', 'INTEGER', False, None),
            ('user_id', 'INTEGER', False, None),
            ('plan_type', 'VARCHAR', False, None),
            ('plan_period', 'VARCHAR', False, None),
            ('plan_content', 'TEXT', False, None),
            ('execution_status', 'TEXT', True, None),
            ('key_obstacles', 'TEXT', True, None),
            ('next_steps', 'TEXT', True, None),
            ('status', 'VARCHAR', False, 'planned'),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('updated_at', 'TIMESTAMPTZ', True, None) 
        ],
        'indexes': [
            'ix_execution_plans_channel_id',
            'ix_execution_plans_user_id',
            'ix_execution_plans_plan_type', 
            'ix_execution_plans_plan_period',
            'ix_execution_plans_status'
        ],
        'fks': [
            'execution_plans_channel_id_fkey',
            'execution_plans_user_id_fkey'
        ]
    },
    'work_orders': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),
            ('cuid_id', 'VARCHAR', True, None),
            ('work_order_no', 'VARCHAR', False, None),
            ('order_type', 'VARCHAR', False, 'CF'),
            ('submitter_id', 'INTEGER', False, None),
            ('related_sales_id', 'INTEGER', True, None),
            ('customer_name', 'VARCHAR', False, None),
            ('customer_contact', 'VARCHAR', True, None),
            ('customer_phone', 'VARCHAR', True, None),
            ('has_channel', 'BOOLEAN', False, 'false'),
            ('channel_id', 'INTEGER', True, None),
            ('channel_name', 'VARCHAR', True, None),
            ('channel_contact', 'VARCHAR', True, None),
            ('channel_phone', 'VARCHAR', True, None),
            ('manufacturer_contact', 'VARCHAR', True, None),
            ('work_type', 'VARCHAR', True, None),
            ('priority', 'VARCHAR', False, 'NORMAL'),
            ('description', 'TEXT', False, None),
            ('status', 'VARCHAR', False, 'PENDING'),
            ('estimated_start_date', 'DATE', True, None),
            ('estimated_start_period', 'VARCHAR', True, None),
            ('estimated_end_date', 'DATE', True, None),
            ('estimated_end_period', 'VARCHAR', True, None),
            ('accepted_at', 'TIMESTAMPTZ', True, None),
            ('started_at', 'TIMESTAMPTZ', True, None),
            ('completed_at', 'TIMESTAMPTZ', True, None),
            ('service_summary', 'TEXT', True, None),
            ('cancel_reason', 'TEXT', True, None),
            ('source_type', 'VARCHAR', True, None),
            ('lead_id', 'INTEGER', True, None),
            ('opportunity_id', 'INTEGER', True, None),
            ('project_id', 'INTEGER', True, None),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('updated_at', 'TIMESTAMPTZ', True, None)
        ],
        'indexes': [
            'ix_work_orders_cuid_id',  # Should map to cuid_id unique index
            'ix_work_orders_work_order_no',  # Should map to work_order_no unique index
            'ix_work_orders_order_type',
            'ix_work_orders_submitter_id',
            'ix_work_orders_related_sales_id',
            'ix_work_orders_channel_id',
            'ix_work_orders_status',
            'ix_work_orders_source_type',
            'ix_work_orders_lead_id',
            'ix_work_orders_opportunity_id', 
            'ix_work_orders_project_id'
        ],
        'fks': [
            'work_orders_submitter_id_fkey',
            'work_orders_related_sales_id_fkey',
            'work_orders_channel_id_fkey',
            'work_orders_lead_id_fkey',
            'work_orders_opportunity_id_fkey',
            'work_orders_project_id_fkey'
        ]
    },
    'evaluations': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),
            ('work_order_id', 'INTEGER', False, None),
            ('quality_rating', 'INTEGER', False, None),
            ('response_rating', 'INTEGER', False, None),
            ('customer_feedback', 'TEXT', True, None),
            ('improvement_suggestion', 'TEXT', True, None),
            ('recommend', 'BOOLEAN', False, 'false'),
            ('evaluator_id', 'INTEGER', False, None),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated')
        ],
        'indexes': [
            'ix_evaluations_work_order_id'  # Unique index
        ],
        'fks': [
            'evaluations_work_order_id_fkey',
            'evaluations_evaluator_id_fkey'
        ],
        'constraints': [
            'evaluations_work_order_id_key'  # UNIQUE constraint on work_order_id
        ]
    },
    'knowledge': {
        'fields': [
            ('id', 'INTEGER', False, 'identity'),
            ('title', 'VARCHAR', False, None),
            ('problem_type', 'VARCHAR', True, None),
            ('problem', 'TEXT', False, None),
            ('solution', 'TEXT', False, None),
            ('tags', 'VARCHAR', True, None),
            ('source_type', 'VARCHAR', False, 'manual'),
            ('source_id', 'INTEGER', True, None),
            ('view_count', 'INTEGER', False, '0'),
            ('created_at', 'TIMESTAMPTZ', True, 'server_generated'),
            ('updated_at', 'TIMESTAMPTZ', True, None)
        ],
        'indexes': [
            'ix_knowledge_title',
            'ix_knowledge_problem_type'
        ],
        'fks': []
    }
}

def connect_to_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def check_table_exists(cur, table_name):
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cur.fetchone()[0]

def get_table_columns(cur, table_name):
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = {}
    for col in cur.fetchall():
        column_name, data_type, is_nullable, column_default = col
        nullable = is_nullable == 'YES'
        
        # Process default for comparison
        processed_default = None
        if column_default:
            # Extract actual default value from "something"::type format
            match = re.search(r"'([^']*).*'|(.*)::", column_default)
            if match:
                processed_default = match.group(1) or match.group(2)   
            # Check for function calls like 'now()'
            elif 'now()' in str(column_default) or 'CURRENT_TIMESTAMP' in str(column_default):
                processed_default = 'server_generated'
            elif any(v in str(column_default).lower() for v in ['false', 'true']):
                processed_default = column_default.strip().lower() == 'true' or column_default.lower().startswith("'t")
            else:
                # Extract literal values like 'planned'::character or 0 or 'CF'::character
                extracted = re.search(r"[\"']([^\"']*)[\"']|(\d+\.?\d*)", str(column_default))
                if extracted:
                    processed_default = extracted.group(1) or extracted.group(2)
                else:
                    processed_default = column_default
                
        columns[column_name] = {
            'type': data_type.upper(),
            'nullable': nullable,
            'default': processed_default
        }
    return columns

def get_table_indexes(cur, table_name):
    cur.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = %s
    """, (table_name,))
    return [row[0] for row in cur.fetchall()]

def get_table_constraints(cur, table_name):
    cur.execute("""
        SELECT conname
        FROM pg_constraint
        JOIN pg_class ON pg_class.oid = pg_constraint.conrelid
        WHERE pg_class.relname = %s
    """, (table_name,))
    return [row[0] for row in cur.fetchall()]

def get_table_fkeys(cur, table_name):
    cur.execute("""
        SELECT conname
        FROM pg_constraint 
        WHERE conrelid = (SELECT oid FROM pg_class WHERE relname = %s)
        AND contype = 'f'
    """, (table_name,))
    return [row[0] for row in cur.fetchall()]

def main():
    print("=== Model vs Database Consistency Checker ===\n")
    
    conn = connect_to_db()
    if not conn:
        print("Cannot connect to database. Exiting.")
        return
    
    try:
        cur = conn.cursor()
        
        issues_found = []
        
        for table_name, expected_def in MODELS_EXPECTED.items():
            print(f"Checking table: {table_name}")
            
            # 1. Check if table exists
            if not check_table_exists(cur, table_name):
                issues_found.append(f"MISSING TABLE: '{table_name}' not found in database")
                print(f"  ❌ MISSING: {table_name} - Table not found!\n")
                continue
            
            print(f"  ✅ EXISTS: {table_name}")
            
            # 2. Check columns
            actual_columns = get_table_columns(cur, table_name)
            
            # Compare expected vs actual columns
            expected_fields = expected_def['fields']
            missing_cols = []
            extra_cols = []
            type_mismatches = []
            
            for field_name, expected_type, expected_nullable, expected_default in expected_fields:
                if field_name not in actual_columns:
                    missing_cols.append(f"{field_name} ({expected_type}, nullable={expected_nullable}, default={expected_default})")
                else:
                    actual_col = actual_columns[field_name]
                    # Compare types - more flexible type matching
                    if not compare_types(actual_col['type'], expected_type):
                        type_mismatches.append(f"{field_name}: Expected {expected_type}, got {actual_col['type']}")
                    
                    # Compare nullable
                    if actual_col['nullable'] != expected_nullable:
                        type_mismatches.append(f"{field_name}: Expected nullable={expected_nullable}, got {actual_col['nullable']}")
                    
                    # Check defaults if expected
                    if expected_default and expected_default != 'identity':
                        # We should be tolerant of 'server_generated' (like now(), CURRENT_TIMESTAMP)
                        # and PostgreSQL function defaults
                        actual_default = str(actual_col['default']).lower() if actual_col['default'] else ''
                        expected_default_lower = str(expected_default).lower()
                        
                        # Skip server-generated defaults checking for now
                        if expected_default_lower != 'server_generated' and \
                           'identity' not in expected_default_lower and \
                           'now()' not in actual_default and \
                           'current_timestamp' not in actual_default:
                            if expected_default_lower not in actual_default:
                                type_mismatches.append(f"{field_name}: Expected default='{expected_default}', got='{actual_col['default']}'")
            
            # Find extra columns that aren't expected
            expected_field_names = [field[0] for field in expected_fields]
            for actual_col_name in actual_columns:
                if actual_col_name not in expected_field_names:
                    extra_cols.append(f"{actual_col_name} ({actual_columns[actual_col_name]['type']})")
            
            if missing_cols or extra_cols or type_mismatches:
                issues_found.extend([f"{table_name}: Missing field - {col}" for col in missing_cols])
                issues_found.extend([f"{table_name}: Extra field - {col}" for col in extra_cols])
                issues_found.extend([f"{table_name}: Type/default mismatch - {mismatch}" for mismatch in type_mismatches])
                
                if missing_cols:
                    print(f"    ❌ Missing fields: {', '.join(missing_cols)}")
                if extra_cols:
                    print(f"    ⚠️  Extra fields: {', '.join(extra_cols)}")  
                if type_mismatches:
                    print(f"    ❌ Type/default mismatches: {', '.join(type_mismatches)}")
            else:
                print(f"    ✅ All fields match expected definition")
            
            # 3. Check indexes
            actual_indexes = get_table_indexes(cur, table_name)
            expected_indexes = expected_def.get('indexes', [])
            
            # Map expected index names to what might actually be generated by PostgreSQL/SQLAlchemy
            actual_indexes_set = set(actual_indexes)
            missing_indexes = []
            found_indexes = []
            
            for expected_idx in expected_indexes:
                # SQLAlchemy may generate slightly different index name patterns
                expected_pattern_clean = re.sub(r'^ix_', '', expected_idx)
                found_in_suffix = False
                for actual_idx in actual_indexes:
                    if expected_pattern_clean in actual_idx or expected_idx in actual_idx:
                        found_in_suffix = True
                        break
                
                if not found_in_suffix:
                    missing_indexes.append(expected_idx)
                else:
                    found_indexes.append(expected_idx)
            
            extra_indexes = []
            # Find actual indexes that don't match expected - exclude primary keys, unique constraints, internal indexes
            for actual_idx in actual_indexes:
                if 'pkey' not in actual_idx and 'sqlite_autoindex' not in actual_idx:
                    # Check if this index name contains parts of any expected index
                    matches_expected = False
                    for expected_idx in expected_indexes:
                        expected_clean = re.sub(r'^ix_|_key$', '', expected_idx)
                        if expected_clean in actual_idx:
                            matches_expected = True
                            break
                    
                    if not matches_expected:
                        # This might be a custom index created from uniqueness constraints
                        # Work order's unique constraints: work_order_no and cuid_id
                        # evaluation's work_order_id unique constraint
                        if table_name == 'work_orders' and ('cuid_id_key' in actual_idx or 'work_order_no_key' in actual_idx):
                            continue # These are OK - they're from unique=True columns  
                        elif table_name == 'evaluations' and 'work_order_id_key' in actual_idx:
                            matches_expected = True  # This is part of 'ix_evaluations_work_order_id' expected
                            continue
                        extra_indexes.append(actual_idx)
            
            if missing_indexes or extra_indexes:
                issues_found.extend([f"{table_name}: Missing index {idx}" for idx in missing_indexes])
                issues_found.extend([f"{table_name}: Extra index {idx}" for idx in extra_indexes])
                
                if missing_indexes:
                    print(f"    ❌ Missing indexes: {missing_indexes}")
                if extra_indexes:
                    print(f"    ⚠️  Extra indexes: {extra_indexes}")
            else:
                print(f"    ✅ Indexes match expected")
            
            # 4. Check Foreign Keys
            actual_fkeys = get_table_fkeys(cur, table_name)
            expected_fks = expected_def.get('fks', [])
            
            missing_fks = []
            extra_fks = []
            
            # For missing FKs, we need a more flexible comparison
            for exp_fk in expected_fks:
                found = False
                # Handle cases where generated names might be slightly different
                exp_name_base = exp_fk.replace('_fkey', '')
                for act_fk in actual_fkeys:
                    if all(part in act_fk for part in exp_name_base.split('_')[0:2]):
                        found = True
                        break
                if not found:
                    missing_fks.append(exp_fk)
                    
            # Extra FKs
            for act_fk in actual_fkeys:
                found = False
                for exp_fk in expected_fks:
                    exp_parts = exp_fk.replace('_fkey', '').split('_')[0:2]  # Use first 2 segments to identify
                    if all(part in act_fk for part in exp_parts):
                        found = True
                        break
                if not found:
                    extra_fks.append(act_fk)
            
            if missing_fks:
                issues_found.extend([f"{table_name}: Missing FK {fkey}" for fkey in missing_fks])
                print(f"    ❌ Missing foreign keys: {missing_fks}")
            elif expected_fks:  # Only show success message if we were expecting fks
                print(f"    ✅ Foreign keys match expected")
                
            if extra_fks:
                print(f"    ⚠️  Extra foreign keys: {extra_fks}")  # Not treated as error unless expected none
                
            print("")
        
        # Print summary of findings
        print("=== SUMMARY ===")
        if issues_found:
            print("❌ Issues detected:")
            for i, issue in enumerate(issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            print("✅ All models match their corresponding database tables perfectly!")
        
        print(f"\nTotal issues found: {len(issues_found)}")
        
    finally:
        conn.close()

def compare_types(actual, expected):
    """Compare if the actual and expected types are compatible."""
    # Normalization: convert common aliases
    actual_upper = actual.upper()
    expected_upper = expected.upper()
    
    # PostgreSQL-specific variations and equivalences (using both directions)
    type_equivalences = {
        ('CHARACTER VARYING', 'VARCHAR'),
        ('CHAR VARYING', 'VARCHAR'),
        ('NATIONAL VARCHAR', 'VARCHAR'),
        ('NVARCHAR', 'VARCHAR'),
        ('TEXT', 'VARCHAR'),  # VARCHAR in models is usually compatible with TEXT in DB
        ('BOOL', 'BOOLEAN'),
        ('BOOLEAN', 'BOOL'),
        ('INT', 'INTEGER'),
        ('INTEGER', 'INT'),
        ('INT4', 'INTEGER'),
        ('INTEGER', 'INT4'),
        ('TIMESTAMP WITH TIME ZONE', 'TIMESTAMPTZ'),
        ('TIMESTAMPTZ', 'TIMESTAMP WITH TIME ZONE'),
        ('TIMESTAMP WITHOUT TIME ZONE', 'TIMESTAMP'),
        ('NUMERIC', 'DECIMAL'),
        ('DECIMAL', 'NUMERIC'),
        ('DATE', 'DATE')
    }
    
    # Exact match
    if actual_upper == expected_upper:
        return True
    
    # Check if this pair is in our equivalences list
    for eq1, eq2 in type_equivalences:
        if (actual_upper == eq1 and expected_upper == eq2) or \
           (actual_upper == eq2 and expected_upper == eq1):
            return True
    
    return False

if __name__ == "__main__":
    main()
