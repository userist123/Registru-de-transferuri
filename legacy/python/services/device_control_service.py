"""
Device Control Service - Scanner Hardware Universal (Endpoint Protector Model)
Scaneaza si monitorizeaza in timp real TOATE mediile de stocare conectate fizic la statie:
1. Stick-uri USB Flash (USBSTOR / VID & PID reale)
2. SSD-uri & HDD-uri Externe (USB / Type-C / Thunderbolt)
3. Unitati Optice CD / DVD / Blu-Ray (CD-ROM / DVD-RW / BD - interne si externe)
4. Unitati SATA / eSATA / Docking Bay / NVMe
5. Carduri de memorie SD / MicroSD / MMC (Card Readers)
Extrage VID/PID, VEN/PROD, Serii Hardware Firmware reale, Litere de Volum si Sisteme de Fisiere.
"""
import re, subprocess, json, platform
from typing import List, Dict, Optional, Tuple
from database.db import DatabaseManager


class DeviceControlService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def scan_connected_devices(self) -> List[Dict]:
        """
        Scaneaza toate mediile de stocare fizice conectate la statie (USB, CD/DVD, SATA, NVMe, SD).
        Potriveste dispozitivele cu registrul de medii amprentate din baza de date.
        """
        devices = []
        if platform.system() == "Windows":
            devices = self._scan_windows_devices()
        else:
            devices = self._scan_posix_mock()

        # Verificare status de autorizare in baza de date a statiei dupa S/N, VID/PID sau Cod Inventar
        for dev in devices:
            matched_medium = self.db.find_medium_by_fingerprint(
                dev.get('vid', ''), dev.get('pid', ''), dev.get('serial_number', '')
            )
            if matched_medium:
                dev['is_amprentat'] = True
                dev['medium_id'] = matched_medium['id']
                dev['nr_inregistrare_mediu'] = matched_medium.get('cod_inventar', 'N/A')
                dev['cod_inventar'] = matched_medium['cod_inventar']
                dev['denumire_custom'] = matched_medium.get('denumire_custom') or dev.get('volume_name') or matched_medium['cod_inventar']
                dev['status_politica'] = matched_medium['status_politica']
                dev['clasificare_max'] = matched_medium['clasificare_max']
                dev['clasificare_max_nato'] = matched_medium.get('clasificare_max_nato', 'NATO UNCLASSIFIED')
                dev['stare_criptare'] = matched_medium.get('stare_criptare', 'Fara')
                dev['gestionar'] = matched_medium.get('gestionar_nume', 'N/A')
            else:
                dev['is_amprentat'] = False
                dev['medium_id'] = None
                dev['nr_inregistrare_mediu'] = "NEÎNREGISTRAT"
                dev['cod_inventar'] = "NEAMPRENTAT"
                if dev.get('is_removable') or dev.get('is_optical'):
                    dev['denumire_custom'] = dev.get('volume_name') or f"{dev.get('tip_mediu', 'Mediu')} ({dev.get('drive_letter', 'N/A')})"
                    dev['status_politica'] = "neamprentat"
                else:
                    dev['denumire_custom'] = f"Disc Intern Stație ({dev.get('drive_letter', 'C:, D:')})"
                    dev['status_politica'] = "disc_intern_sistem"
                dev['clasificare_max'] = "N/A"
                dev['clasificare_max_nato'] = "N/A"
                dev['stare_criptare'] = "Necunoscut"
                dev['gestionar'] = "N/A"

        return devices

    def _scan_windows_devices(self) -> List[Dict]:
        devices = []
        ps_code = """
$allDisks = @()

# 1. Scan Physical Disks (USB, SATA, NVMe, SD)
$drives = Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue
foreach ($d in $drives) {
    $parts = Get-CimAssociatedInstance -InputObject $d -ResultClassName Win32_DiskPartition -ErrorAction SilentlyContinue
    $vols = @()
    if ($parts) {
        foreach ($p in $parts) {
            $log = Get-CimAssociatedInstance -InputObject $p -ResultClassName Win32_LogicalDisk -ErrorAction SilentlyContinue
            if ($log) {
                foreach ($l in $log) {
                    $vols += [PSCustomObject]@{
                        Letter = $l.DeviceID
                        Label = $l.VolumeName
                        FileSystem = $l.FileSystem
                        FreeGB = [Math]::Round($l.FreeSpace / 1GB, 2)
                        TotalGB = [Math]::Round($l.Size / 1GB, 2)
                        VolumeSerial = $l.VolumeSerialNumber
                    }
                }
            }
        }
    }
    $allDisks += [PSCustomObject]@{
        DeviceType = "Disk"
        Model = $d.Model
        InterfaceType = $d.InterfaceType
        MediaType = $d.MediaType
        PNPDeviceID = $d.PNPDeviceID
        SerialNumber = ($d.SerialNumber -replace '^\\s+|\\s+$', '')
        SizeGB = [Math]::Round($d.Size / 1GB, 2)
        Volumes = $vols
    }
}

# 2. Scan Optical Drives (CD/DVD/Blu-Ray)
$cdroms = Get-CimInstance Win32_CDROMDrive -ErrorAction SilentlyContinue
foreach ($cd in $cdroms) {
    $vols = @()
    if ($cd.Drive) {
        $log = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($cd.Drive)'" -ErrorAction SilentlyContinue
        if ($log) {
            $vols += [PSCustomObject]@{
                Letter = $log.DeviceID
                Label = $log.VolumeName
                FileSystem = $log.FileSystem
                FreeGB = 0.0
                TotalGB = [Math]::Round($log.Size / 1GB, 2)
                VolumeSerial = $log.VolumeSerialNumber
            }
        }
    }
    $allDisks += [PSCustomObject]@{
        DeviceType = "CDROM"
        Model = $cd.Name
        InterfaceType = "OPTICAL"
        MediaType = "CD/DVD Optical Disc"
        PNPDeviceID = $cd.PNPDeviceID
        SerialNumber = ($cd.SerialNumber -replace '^\\s+|\\s+$', '')
        SizeGB = 0.0
        Volumes = $vols
        MediaLoaded = $cd.MediaLoaded
    }
}

$allDisks | ConvertTo-Json -Depth 4 -Compress
"""
        try:
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, text=True, timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout.strip())
                if isinstance(raw, dict):
                    raw = [raw]

                for item in raw:
                    dev_type = item.get('DeviceType', 'Disk')
                    pnp = item.get('PNPDeviceID', '') or ''
                    raw_serial = (item.get('SerialNumber') or '').strip()
                    model = (item.get('Model') or 'Storage Device').strip()
                    interface = (item.get('InterfaceType') or '').strip().upper()
                    media_type_raw = (item.get('MediaType') or '').strip()
                    size_gb = float(item.get('SizeGB') or 0.0)
                    
                    vols = item.get('Volumes') or []
                    if isinstance(vols, dict):
                        vols = [vols]

                    letters_list = [v.get('Letter') for v in vols if v.get('Letter')]
                    letters_str = ", ".join(letters_list) if letters_list else "Fără literă"
                    
                    labels_list = [v.get('Label') for v in vols if v.get('Label')]
                    vol_name = ", ".join(labels_list) if labels_list else ""
                    
                    fs_list = list(set([v.get('FileSystem') for v in vols if v.get('FileSystem')]))
                    fs_str = ", ".join(fs_list) if fs_list else ("UDF/CDFS" if dev_type == "CDROM" else "NTFS")
                    
                    vol_serials = [v.get('VolumeSerial') for v in vols if v.get('VolumeSerial')]
                    vol_sn = ", ".join(vol_serials) if vol_serials else ""

                    free_gb = sum([float(v.get('FreeGB') or 0.0) for v in vols])
                    free_gb = round(free_gb, 2)

                    is_optical = (dev_type == 'CDROM') or ('CDROM' in pnp.upper()) or ('OPTICAL' in interface)
                    is_usb = (interface == 'USB') or ('USB' in pnp.upper()) or ('USBSTOR' in pnp.upper())
                    is_sd = ('SD' in pnp.upper()) or ('CARDREADER' in model.upper()) or ('MMC' in model.upper())
                    is_removable = is_usb or is_optical or is_sd or ('REMOVABLE' in media_type_raw.upper()) or ('EXTERNAL' in media_type_raw.upper())
                    
                    vid, pid, sn = self._parse_hardware_ids(pnp, raw_serial, is_usb, is_optical, model)

                    # Tip mediu detaliat
                    if is_optical:
                        tip_mediu = "Unitate Optică (CD / DVD / Blu-Ray)"
                    elif is_sd:
                        tip_mediu = "Card Memorie (SD / MicroSD / MMC)"
                    elif is_usb:
                        if size_gb <= 128 and ('REMOVABLE' in media_type_raw.upper() or 'FLASH' in model.upper() or 'USB' in model.upper()):
                            tip_mediu = "Stick USB Flash"
                        elif 'SSD' in model.upper() or 'NVME' in model.upper():
                            tip_mediu = "SSD Extern (USB / Type-C)"
                        else:
                            tip_mediu = "HDD Extern (USB / SATA Extern)"
                    elif 'SATA' in interface or 'IDE' in interface:
                        tip_mediu = "Disc SATA / eSATA"
                    elif 'NVME' in model.upper() or 'NVME' in pnp.upper():
                        tip_mediu = "Disc Intern Fix (NVMe SSD)"
                    elif 'SSD' in model.upper():
                        tip_mediu = "Disc Intern Fix (SATA SSD)"
                    else:
                        tip_mediu = "Disc Intern Fix (HDD/SATA)"

                    devices.append({
                        'model': model,
                        'producator': self._extract_vendor(model),
                        'interface_type': interface,
                        'media_type_raw': media_type_raw,
                        'is_removable': is_removable,
                        'is_optical': is_optical,
                        'tip_mediu': tip_mediu,
                        'pnp_device_id': pnp,
                        'vid': vid,
                        'pid': pid,
                        'serial_number': sn,
                        'drive_letter': letters_str,
                        'volume_name': vol_name,
                        'file_system': fs_str,
                        'volume_serial': vol_sn,
                        'capacitate_gb': size_gb,
                        'liber_gb': free_gb
                    })
        except Exception:
            pass

        return devices

    def _scan_posix_mock(self) -> List[Dict]:
        return [
            {
                'model': 'Secure Military USB (Posix)',
                'producator': 'Kingston',
                'interface_type': 'USB',
                'media_type_raw': 'Removable Media',
                'is_removable': True,
                'is_optical': False,
                'tip_mediu': 'Stick USB Flash',
                'pnp_device_id': 'USB\\VID_0951&PID_1666\\001A2B3C4D',
                'vid': '0951',
                'pid': '1666',
                'serial_number': '001A2B3C4D',
                'drive_letter': '/media/usb0',
                'volume_name': 'MAPN_SEC_USB',
                'file_system': 'ext4',
                'volume_serial': 'VOL-POSIX-99',
                'capacitate_gb': 64.0,
                'liber_gb': 42.5
            },
            {
                'model': 'DVD-RW Drive (Posix)',
                'producator': 'LG',
                'interface_type': 'OPTICAL',
                'media_type_raw': 'CD/DVD Optical Disc',
                'is_removable': True,
                'is_optical': True,
                'tip_mediu': 'Unitate Optică (CD / DVD / Blu-Ray)',
                'pnp_device_id': 'SCSI\\CDROM&VEN_LG&PROD_DVDRAM\\001',
                'vid': 'VEN_LG',
                'pid': 'PROD_DVDRAM',
                'serial_number': 'SN-OPTICAL-01',
                'drive_letter': '/dev/cdrom',
                'volume_name': 'DISC_RAPORT_2026',
                'file_system': 'iso9660',
                'volume_serial': 'VOL-ISO-01',
                'capacitate_gb': 4.7,
                'liber_gb': 0.0
            }
        ]

    def _parse_hardware_ids(self, pnp: str, raw_serial: str, is_usb: bool, is_optical: bool, model: str) -> Tuple[str, str, str]:
        vid = "N/A"
        pid = "N/A"
        
        if is_usb:
            vid = "0000"
            pid = "0000"
            vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', pnp)
            if vid_match:
                vid = vid_match.group(1).upper()
            pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', pnp)
            if pid_match:
                pid = pid_match.group(1).upper()
        else:
            # Extract VEN_xxxx and PROD_yyyy from SCSI/SATA/CDROM PNP ID
            ven_match = re.search(r'VEN_([^&]+)', pnp)
            prod_match = re.search(r'PROD_([^&]+)', pnp)
            if ven_match and prod_match:
                vid = f"VEN_{ven_match.group(1)[:6].strip()}"
                pid = f"PROD_{prod_match.group(1)[:8].strip()}"
            elif is_optical:
                vid = "OPTICAL"
                pid = "CD/DVD"

        sn = raw_serial.strip() if raw_serial else ""
        if not sn or sn == "0" or "&" in sn:
            parts = pnp.split('\\')
            if len(parts) >= 3:
                candidate = parts[-1]
                if "&" in candidate:
                    sn = candidate.split('&')[0]
                else:
                    sn = candidate

        if not sn:
            if is_usb:
                sn = f"SN-USB-{vid}-{pid}"
            elif is_optical:
                sn = f"SN-OPTICAL-{abs(hash(model)) % 100000000:08d}"
            else:
                sn = f"SN-DISK-{abs(hash(pnp)) % 100000000:08d}"

        return vid, pid, sn

    def _extract_vendor(self, model: str) -> str:
        common = [
            "SanDisk", "Kingston", "Samsung", "Corsair", "Transcend", "Crucial",
            "Western Digital", "WD", "Seagate", "Toshiba", "Micron", "Kioxia",
            "Intel", "SK Hynix", "LG", "ASUS", "Lite-On", "Pioneer", "Sony", "Hitachi"
        ]
        for c in common:
            if c.lower() in model.lower():
                return c
        return model.split(' ')[0] if model else "Generic"
