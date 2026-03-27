import logging
import pandas as pd
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Tuple, Optional

from django.db import transaction
from django.db.models import Q

from properties.models import Property
from daily_metrics.models import DailyPropertyReport
from daily_metrics.serializers.property_report_upload_serializer import (
    DailyPropertyReportSerializer
)

logger = logging.getLogger(__name__)


class PropertyReportImportService:
    """
    Service class for importing daily property metrics from CSV/XLSX files.
    
    Handles parsing, validation, property mapping, and upsert operations
    for daily property reports.
    """
    
    # Required columns in the uploaded file
    REQUIRED_COLUMNS = [
        'date', 'hotel', 'rooms', 'arrivals', 'departures', 'stay_over',
        'total_income', 'average_room_rate', 'bed_nights', 'average_guest_rate',
        'occupancy_percentage', 'guest_per_room'
    ]
    
    # Column name mappings (normalize various column name formats)
    COLUMN_MAPPINGS = {
        'date': 'date',
        'hotel': 'hotel',
        'property': 'hotel',
        'property_name': 'hotel',
        'rooms': 'rooms',
        'room_count': 'rooms',
        'arrivals': 'arrivals',
        'arrival': 'arrivals',
        'departures': 'departures',
        'departure': 'departures',
        'stay_over': 'stay_over',
        'stayover': 'stay_over',
        'total_income': 'total_income',
        'revenue': 'total_income',
        'income': 'total_income',
        'average_room_rate': 'average_room_rate',
        'avg_room_rate': 'average_room_rate',
        'arr': 'average_room_rate',
        'bed_nights': 'bed_nights',
        'bednights': 'bed_nights',
        'nights': 'bed_nights',
        'average_guest_rate': 'average_guest_rate',
        'avg_guest_rate': 'average_guest_rate',
        'agr': 'average_guest_rate',
        'occupancy_percentage': 'occupancy_percentage',
        'occupancy': 'occupancy_percentage',
        'occ': 'occupancy_percentage',
        'guest_per_room': 'guest_per_room',
        'gpr': 'guest_per_room',
        'unit': 'unit',
        'room_type': 'room_type',
    }
    
    def __init__(self, data_type: str = 'actual', dry_run: bool = False):
        """
        Initialize the import service.
        
        Args:
            data_type: The type of data being imported ('actual' or 'otb')
            dry_run: If True, validate data without saving to database
        """
        self.data_type = data_type.lower()
        self.dry_run = dry_run
        self.created = 0
        self.updated = 0
        self.errors: List[Dict[str, Any]] = []
        
    def process_file(self, file) -> Dict[str, Any]:
        """
        Process the uploaded file and import the data.
        
        Args:
            file: The uploaded file object (CSV or XLSX)
            
        Returns:
            Dict containing the results of the import operation
        """
        try:
            # Parse the file using pandas
            df = self._parse_file(file)
            
            if df is None or df.empty:
                return {
                    'status': 'failed',
                    'created': 0,
                    'updated': 0,
                    'errors': [{'row': 0, 'error': 'File is empty or could not be parsed'}]
                }
            
            # Normalize column names
            df = self._normalize_columns(df)
            
            # Validate required columns
            validation_error = self._validate_required_columns(df)
            if validation_error:
                return {
                    'status': 'failed',
                    'created': 0,
                    'updated': 0,
                    'errors': [validation_error]
                }
            
            # Process each row
            return self._process_rows(df)
            
        except Exception as e:
            logger.exception("Error processing file")
            return {
                'status': 'failed',
                'created': 0,
                'updated': 0,
                'errors': [{'row': 0, 'error': f'Failed to process file: {str(e)}'}]
            }
    
    def _parse_file(self, file) -> Optional[pd.DataFrame]:
        """
        Parse the uploaded file using pandas.
        
        Args:
            file: The uploaded file object
            
        Returns:
            DataFrame containing the parsed data, or None if parsing fails
        """
        file_name = file.name.lower()
        
        try:
            if file_name.endswith('.csv'):
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(file, encoding=encoding)
                        if not df.empty:
                            return df
                    except UnicodeDecodeError:
                        continue
                return pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
                
            elif file_name.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file)
            
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise
        
        return None
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to the expected format.
        
        Args:
            df: DataFrame with potentially varying column names
            
        Returns:
            DataFrame with normalized column names
        """
        # Convert column names to lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        # Map columns to expected names
        renamed_columns = {}
        for col in df.columns:
            if col in self.COLUMN_MAPPINGS:
                renamed_columns[col] = self.COLUMN_MAPPINGS[col]
        
        df = df.rename(columns=renamed_columns)
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _validate_required_columns(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Validate that all required columns are present.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Error dict if validation fails, None otherwise
        """
        missing_columns = []
        
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return {
                'row': 0,
                'error': f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        return None
    
    def _process_rows(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process all rows in the DataFrame.
        
        Args:
            df: DataFrame containing the data to process
            
        Returns:
            Dict containing the results of the import operation
        """
        # Reset counters
        self.created = 0
        self.updated = 0
        self.errors = []
        
        # Prefetch existing properties for efficiency
        property_cache = self._build_property_cache()
        
        # Process each row
        with transaction.atomic():
            for row_num, row in df.iterrows():
                row_result = self._process_single_row(
                    row, 
                    row_num + 2,  # +2 to account for header and 0-indexing
                    property_cache
                )
                
                if row_result.get('error'):
                    self.errors.append(row_result)
                elif row_result.get('created'):
                    self.created += 1
                elif row_result.get('updated'):
                    self.updated += 1
        
        # Determine overall status
        if self.errors and self.created == 0 and self.updated == 0:
            status = 'failed'
        elif self.errors:
            status = 'completed_with_errors'
        else:
            status = 'success'
        
        return {
            'status': status,
            'created': self.created,
            'updated': self.updated,
            'errors': self.errors
        }
    
    def _build_property_cache(self) -> Dict[str, Property]:
        """
        Build a cache of existing properties for efficient lookup.
        
        Returns:
            Dict mapping property names to Property objects
        """
        properties = Property.objects.all()
        return {p.name.lower(): p for p in properties}
    
    def _process_single_row(
        self, 
        row: pd.Series, 
        row_num: int,
        property_cache: Dict[str, Property]
    ) -> Dict[str, Any]:
        """
        Process a single row from the DataFrame.
        
        Args:
            row: Series containing the row data
            row_num: The row number (for error reporting)
            property_cache: Cache of existing properties
            
        Returns:
            Dict indicating the result of processing this row
        """
        try:
            # Validate and extract data
            validated_data = self._validate_row(row, row_num)
            
            if validated_data is None:
                return {'error': f"Row {row_num}: Validation failed"}
            
            # Get or create property
            property_obj = self._get_or_create_property(
                validated_data['hotel'],
                validated_data.get('unit'),
                validated_data.get('room_type'),
                property_cache
            )
            
            if property_obj is None:
                return {
                    'error': f"Row {row_num}: Could not create property '{validated_data['hotel']}'"
                }
            
            # If dry run, just validate
            if self.dry_run:
                return {'validated': True}
            
            # Upsert the daily report
            created, updated = self._upsert_daily_report(
                property_obj,
                validated_data
            )
            
            return {'created': created, 'updated': updated}
            
        except Exception as e:
            logger.exception(f"Error processing row {row_num}")
            return {'error': f"Row {row_num}: {str(e)}"}
    
    def _validate_row(
        self, 
        row: pd.Series, 
        row_num: int
    ) -> Optional[Dict[str, Any]]:
        """
        Validate and extract data from a row.
        
        Args:
            row: Series containing the row data
            row_num: The row number (for error reporting)
            
        Returns:
            Validated data dict, or None if validation fails
        """
        try:
            # Convert row to dict
            data = row.to_dict()
            
            # Parse date
            date_value = data.get('date')
            if pd.isna(date_value) or str(date_value).strip() == '':
                self.errors.append({'row': row_num, 'error': 'Date is required'})
                return None
            
            try:
                if isinstance(date_value, str):
                    # Try various date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            parsed_date = datetime.strptime(str(date_value), fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        self.errors.append({
                            'row': row_num, 
                            'error': f"Invalid date format: {date_value}"
                        })
                        return None
                else:
                    parsed_date = pd.to_datetime(date_value).date()
            except Exception:
                self.errors.append({'row': row_num, 'error': f"Invalid date: {date_value}"})
                return None
            
            # Extract and validate fields
            validated = {
                'date': parsed_date,
                'hotel': str(data.get('hotel', '')).strip(),
                'rooms': self._parse_integer(data.get('rooms'), 'rooms', row_num),
                'arrivals': self._parse_integer(data.get('arrivals'), 'arrivals', row_num),
                'departures': self._parse_integer(data.get('departures'), 'departures', row_num),
                'stay_over': self._parse_integer(data.get('stay_over'), 'stay_over', row_num),
                'total_income': self._parse_decimal(data.get('total_income'), 'total_income', row_num),
                'average_room_rate': self._parse_decimal(data.get('average_room_rate'), 'average_room_rate', row_num),
                'bed_nights': self._parse_integer(data.get('bed_nights'), 'bed_nights', row_num),
                'average_guest_rate': self._parse_decimal(data.get('average_guest_rate'), 'average_guest_rate', row_num),
                'occupancy_percentage': self._parse_decimal(data.get('occupancy_percentage'), 'occupancy_percentage', row_num, max_value=100),
                'guest_per_room': self._parse_decimal(data.get('guest_per_room'), 'guest_per_room', row_num),
            }
            
            # Validate required fields
            if not validated['hotel']:
                self.errors.append({'row': row_num, 'error': 'Hotel name is required'})
                return None
            
            # Check for validation failures
            for field in ['rooms', 'arrivals', 'departures', 'stay_over', 'bed_nights']:
                if validated[field] is None:
                    return None
            
            for field in ['total_income', 'average_room_rate', 'average_guest_rate', 'occupancy_percentage', 'guest_per_room']:
                if validated[field] is None:
                    return None
            
            # Optional fields
            validated['unit'] = str(data.get('unit', '')).strip() if pd.notna(data.get('unit')) else None
            validated['room_type'] = str(data.get('room_type', '')).strip() if pd.notna(data.get('room_type')) else None
            
            return validated
            
        except Exception as e:
            logger.exception(f"Error validating row {row_num}")
            self.errors.append({'row': row_num, 'error': str(e)})
            return None
    
    def _parse_integer(
        self, 
        value: Any, 
        field_name: str, 
        row_num: int
    ) -> Optional[int]:
        """Parse and validate an integer field."""
        if pd.isna(value):
            self.errors.append({'row': row_num, 'error': f'{field_name} is required'})
            return None
        
        try:
            result = int(float(value))
            if result < 0:
                self.errors.append({
                    'row': row_num, 
                    'error': f'{field_name} must be non-negative'
                })
                return None
            return result
        except (ValueError, TypeError):
            self.errors.append({
                'row': row_num, 
                'error': f'Invalid {field_name}: {value}'
            })
            return None
    
    def _parse_decimal(
        self, 
        value: Any, 
        field_name: str, 
        row_num: int,
        max_value: float = None
    ) -> Optional[Decimal]:
        """Parse and validate a decimal field."""
        if pd.isna(value):
            self.errors.append({'row': row_num, 'error': f'{field_name} is required'})
            return None
        
        try:
            result = Decimal(str(value))
            if result < 0:
                self.errors.append({
                    'row': row_num, 
                    'error': f'{field_name} must be non-negative'
                })
                return None
            if max_value is not None and result > max_value:
                self.errors.append({
                    'row': row_num, 
                    'error': f'{field_name} must be <= {max_value}'
                })
                return None
            return result
        except (InvalidOperation, ValueError, TypeError):
            self.errors.append({
                'row': row_num, 
                'error': f'Invalid {field_name}: {value}'
            })
            return None
    
    def _get_or_create_property(
        self,
        hotel_name: str,
        unit: Optional[str],
        room_type: Optional[str],
        property_cache: Dict[str, Property]
    ) -> Optional[Property]:
        """
        Get or create a property based on the hotel name.
        
        Args:
            hotel_name: Name of the hotel/property
            unit: Unit type (optional)
            room_type: Room type (optional)
            property_cache: Cache of existing properties
            
        Returns:
            Property object, or None if creation fails
        """
        # Check cache first
        cache_key = hotel_name.lower()
        if cache_key in property_cache:
            return property_cache[cache_key]
        
        # Check if property exists in database
        property_obj = Property.objects.filter(
            name__iexact=hotel_name
        ).first()
        
        if property_obj:
            property_cache[cache_key] = property_obj
            return property_obj
        
        # Create new property
        try:
            property_obj = Property.objects.create(
                name=hotel_name,
                address='',  # Required field, set to empty
                type='apartment',  # Default type
                manager='',  # Required field, set to empty
                unit=unit if unit else None,
                number_of_rooms=1,
                room_type=room_type if room_type else None
            )
            property_cache[cache_key] = property_obj
            return property_obj
            
        except Exception as e:
            logger.error(f"Error creating property '{hotel_name}': {e}")
            return None
    
    def _upsert_daily_report(
        self,
        property_obj: Property,
        validated_data: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        """
        Insert or update a daily property report.
        
        Args:
            property_obj: The Property object
            validated_data: Validated row data
            
        Returns:
            Tuple of (created, updated) booleans
        """
        defaults = {
            'rooms': validated_data['rooms'],
            'arrivals': validated_data['arrivals'],
            'departures': validated_data['departures'],
            'stay_over': validated_data['stay_over'],
            'total_income': validated_data['total_income'],
            'avg_room_rate': validated_data['average_room_rate'],
            'bed_nights': validated_data['bed_nights'],
            'avg_guest_rate': validated_data['average_guest_rate'],
            'occupancy_percentage': validated_data['occupancy_percentage'],
            'guest_per_room': validated_data['guest_per_room'],
        }
        
        report, created = DailyPropertyReport.objects.update_or_create(
            property=property_obj,
            date=validated_data['date'],
            data_type=self.data_type,
            defaults=defaults
        )
        
        return (created, not created)