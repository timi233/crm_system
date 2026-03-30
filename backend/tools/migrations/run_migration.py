"""
Migration execution script for CRM system.
This script executes the complete data migration process.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path to import migration framework
sys.path.append(str(Path(__file__).parent.parent))

from tools.crm_data_migration import DataMigrationFramework
from tools.migration_config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to execute the data migration."""
    
    logger.info("Starting CRM data migration execution...")
    logger.info(f"Source data path: {config.SOURCE_DATA_PATH}")
    logger.info(f"Database URL: {config.DATABASE_URL}")
    logger.info(f"Dry run mode: {config.DRY_RUN}")
    
    try:
        # Initialize migration framework
        migration = DataMigrationFramework(
            db_url=config.DATABASE_URL,
            source_data_path=str(config.SOURCE_DATA_PATH)
        )
        
        # Check if dry run mode is enabled
        if config.DRY_RUN:
            logger.info("DRY RUN MODE: Only validation will be performed, no actual migration")
            # Perform validation only
            validate_source_data(config.SOURCE_DATA_PATH)
            logger.info("Dry run completed successfully!")
            return
        
        # Execute actual migration
        result = migration.run_migration()
        
        if result['success']:
            logger.info("Migration completed successfully!")
            logger.info(f"Migration statistics: {json.dumps(result['stats'], indent=2)}")
            
            # Generate migration report
            report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'stats': result['stats'],
                    'source_path': str(config.SOURCE_DATA_PATH),
                    'database_url': config.DATABASE_URL
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Migration report saved to: {report_file}")
            
            # Print summary
            print("\n" + "="*50)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("="*50)
            print(f"Customers migrated: {result['stats']['customers']['migrated']}")
            print(f"Opportunities migrated: {result['stats']['opportunities']['migrated']}")
            print(f"Contracts migrated: {result['stats']['contracts']['migrated']}")
            print(f"Products standardized: {result['stats']['products']['standardized']}")
            print(f"Duplicate customers resolved: {result['stats']['customers']['duplicates']}")
            print("="*50)
            
        else:
            logger.error("Migration failed!")
            logger.error(f"Errors: {result['errors']}")
            
            print("\n" + "="*50)
            print("MIGRATION FAILED")
            print("="*50)
            for error in result['errors']:
                print(f"Error: {error}")
            print("="*50)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        logger.exception(e)
        print(f"\nMigration failed with unexpected error: {str(e)}")
        sys.exit(1)

def validate_source_data(source_path: Path):
    """Validate source data without performing actual migration."""
    logger.info("Validating source data structure...")
    
    # Check if source path exists
    if not source_path.exists():
        logger.warning(f"Source path does not exist: {source_path}")
        return
    
    # Check for required files
    required_files = [
        'crm_schema_dump.json',
        'crm_views_dump.json',
        'crm_readonly_stats.json'
    ]
    
    found_files = []
    for file in required_files:
        if (source_path / file).exists():
            found_files.append(file)
            logger.info(f"Found required file: {file}")
        else:
            logger.warning(f"Missing required file: {file}")
    
    # Check for Excel files
    excel_files = list(source_path.glob("*.xlsx"))
    if excel_files:
        latest_excel = max(excel_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Found Excel file: {latest_excel.name}")
        found_files.append(latest_excel.name)
    
    if not found_files:
        logger.warning("No source data files found!")
        logger.info("Falling back to synthetic data generation...")
    
    logger.info("Source data validation completed")

if __name__ == "__main__":
    main()