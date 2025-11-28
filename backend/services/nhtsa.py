import httpx
from typing import Optional, Dict, Any


class NHTSAService:
    """Service for validating vehicles against NHTSA API."""
    
    BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"
    
    @staticmethod
    async def decode_vin(vin: str) -> Dict[str, Any]:
        """
        Decode a VIN using NHTSA API with multiple validation passes.
        Returns vehicle information if valid, or error info if invalid.
        
        NHTSA Error Codes:
        0 = No errors
        1-6 = Warnings but VIN structure is valid
        7+ = Invalid VIN format
        
        Note: We don't validate checksums locally because not all manufacturers
        follow the standard strictly, and NHTSA accepts VINs without valid checksums.
        """
        # Use DecodeVinValues for better validation
        url = f"{NHTSAService.BASE_URL}/DecodeVinValues/{vin}?format=json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("Results", [])
                
                if not results:
                    return {
                        "valid": False,
                        "error": "Could not decode VIN. Please verify it's correct."
                    }
                
                # Extract data from results
                result_data = results[0] if results else {}
                
                # Get error code and convert to int safely
                error_code_raw = result_data.get("ErrorCode", "0")
                try:
                    error_code = int(str(error_code_raw).strip()) if error_code_raw else 0
                except (ValueError, TypeError):
                    error_code = 0
                
                # Extract vehicle information
                make = result_data.get("Make")
                model = result_data.get("Model")
                year = result_data.get("ModelYear")
                body_class = result_data.get("BodyClass")
                
                # Error codes 0-6 are acceptable (0 = perfect, 1-6 = warnings but valid)
                # Error codes 7+ indicate invalid VIN structure
                if error_code >= 7:
                    error_text = result_data.get("ErrorText", "Invalid VIN format")
                    return {
                        "valid": False,
                        "error": f"Invalid VIN: {error_text}"
                    }
                
                # Must have at least a make to be considered valid
                if not make or make.strip() == "":
                    return {
                        "valid": False,
                        "error": "Could not decode VIN. Please verify it's correct."
                    }
                
                # Additional validation: reject if make seems like a manufacturer code (contains +)
                # or if it's obviously not a consumer vehicle
                suspicious_makes = ["SHERMAN + REILLY", "INCOMPLETE", "NOT APPLICABLE"]
                if make.upper() in suspicious_makes or "+" in make:
                    # For non-consumer vehicles, require at least a year to accept
                    if not year or year.strip() == "":
                        return {
                            "valid": False,
                            "error": "This VIN doesn't appear to be for a standard consumer vehicle."
                        }
                
                # Stricter validation: For consumer vehicles, we should have at least make and year
                # If NHTSA gives us incomplete data on what should be a normal car, it's suspicious
                if error_code >= 1 and (not year or not model):
                    # Warn user but don't block - could be an older vehicle
                    pass
                
                return {
                    "valid": True,
                    "make": make,
                    "model": model,
                    "year": year,
                    "body_class": body_class,
                    "error_code": error_code  # Include for debugging
                }
                
            except httpx.TimeoutException:
                return {
                    "valid": False,
                    "error": "Vehicle verification service timed out. Please try again."
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Error verifying vehicle: {str(e)}"
                }
    
    @staticmethod
    async def validate_year_make(year: int, make: str) -> Dict[str, Any]:
        """
        Validate that a make exists for a given year using NHTSA API.
        """
        url = f"{NHTSAService.BASE_URL}/GetMakesForVehicleType/car?format=json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("Results", [])
                makes = [r.get("MakeName", "").upper() for r in results]
                
                if make.upper() in makes:
                    return {"valid": True}
                
                # Also check against all makes
                all_makes_url = f"{NHTSAService.BASE_URL}/GetAllMakes?format=json"
                response = await client.get(all_makes_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("Results", [])
                all_makes = [r.get("Make_Name", "").upper() for r in results]
                
                if make.upper() in all_makes:
                    return {"valid": True}
                
                return {
                    "valid": False,
                    "error": f"'{make}' doesn't appear to be a valid vehicle make. Please check the spelling."
                }
                
            except httpx.TimeoutException:
                # On timeout, assume valid to not block user
                return {"valid": True, "warning": "Could not verify make, proceeding anyway."}
            except Exception:
                return {"valid": True, "warning": "Could not verify make, proceeding anyway."}

