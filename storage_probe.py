import subprocess
import os
import re

def probe_storage_type():
    """
    Probe the system's primary storage device.
    Returns information about the storage type, size, and category.
    """

    try:
        if os.name == 'nt':  # Windows
            # Get system drive information using PowerShell
            system_drive = os.environ.get('SystemDrive', 'C:')
            
            # First try to get detailed information with PowerShell
            try:
                ps_cmd = f"""
                $disk = Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq 
                    (Get-Partition -DriveLetter '{system_drive[0]}' | Get-Disk).Number}}
                $size = [math]::Round($disk.Size / 1GB, 2)
                $type = $disk.MediaType
                $model = $disk.FriendlyName
                "$type|$size|$model"
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, check=True
                )
                
                output = result.stdout.strip()
                if output:
                    parts = output.split('|')
                    if len(parts) >= 3:
                        media_type = parts[0].strip()
                        size_gb = float(parts[1].strip())
                        model = parts[2].strip()
                        
                        # Determine storage type and category
                        storage_type = f"{model} ({media_type})"
                        
                        if "SSD" in media_type or "SSD" in model:
                            category = "high"
                        elif "NVMe" in media_type or "NVMe" in model:
                            category = "high"
                        elif "HDD" in media_type or "HDD" in model:
                            category = "low"
                        else:
                            category = "mid"
                        
                        return {
                            "ok": True, 
                            "type": f"{storage_type} - {size_gb} GB", 
                            "size_gb": size_gb,
                            "category": category
                        }
            except Exception as e:
                print(f"PowerShell method failed: {e}")
                # Continue to fallback method
            
            # Fallback to WMIC if PowerShell method fails. And pray it works lmao 
            out = subprocess.check_output(
                ["wmic", "diskdrive", "get", "model,mediaType,size"],
                text=True
            ).strip().splitlines()
            
            # Filter and process lines
            data_lines = [l.strip() for l in out if l.strip() and "model" not in l.lower()]
            if not data_lines:
                return {"ok": False, "type": None, "category": "unknown", "error": "No storage devices found"}
            
            # Process the first disk (usually the system disk)
            first_line = data_lines[0].lower()
            
            # Try to extract size
            size_match = re.search(r'(\d+)$', first_line)
            size_gb = 0
            if size_match:
                try:
                    # Convert bytes to GB 
                    size_gb = round(int(size_match.group(1)) / (1024**3), 2)
                    first_line = f"{first_line} ({size_gb} GB)"
                except:
                    pass
            
            # Determine category
            if "nvme" in first_line:
                cat = "high"
            elif "ssd" in first_line:
                cat = "high"
            elif "hdd" in first_line or "hard disk" in first_line:
                cat = "low"
            else:
                cat = "mid"
            
            return {"ok": True, "type": first_line, "size_gb": size_gb, "category": cat}
        
       
        
    except Exception as e:
        return {"ok": False, "type": None, "category": "unknown", "error": str(e)}

if __name__ == "__main__":
    print(probe_storage_type())
