"""
Rights Ledger for Inscenium
============================

Manage placement rights, licensing, and compliance tracking for
brand placement opportunities in scene graph intelligence.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class RightsStatus(Enum):
    """Status of placement rights"""
    AVAILABLE = "available"
    RESERVED = "reserved" 
    LICENSED = "licensed"
    EXPIRED = "expired"
    CONTESTED = "contested"
    BLOCKED = "blocked"

class PlacementType(Enum):
    """Type of brand placement"""
    LOGO_OVERLAY = "logo_overlay"
    PRODUCT_PLACEMENT = "product_placement"
    BILLBOARD_AD = "billboard_ad"
    SCREEN_CONTENT = "screen_content"
    VIRTUAL_INSERTION = "virtual_insertion"

@dataclass
class RightsEntry:
    """Rights entry for a placement opportunity"""
    entry_id: str
    surface_id: str
    title_id: str
    shot_id: str
    placement_type: PlacementType
    status: RightsStatus
    rights_holder: Optional[str]
    licensee: Optional[str] 
    license_start: Optional[datetime]
    license_end: Optional[datetime]
    territory: List[str]  # Geographic territories
    media_rights: List[str]  # Media distribution rights
    exclusivity: bool
    revenue_share: Optional[float]
    placement_fee: Optional[float]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class LicenseTerms:
    """License terms for placement rights"""
    duration_months: int
    territory: List[str]
    media_rights: List[str]
    exclusivity: bool
    revenue_share: float  # Percentage (0-100)
    minimum_fee: float
    usage_restrictions: List[str]
    brand_safety_requirements: Dict[str, Any]

class RightsLedger:
    """Manage placement rights and licensing"""
    
    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or Path("rights_ledger.json")
        self.entries: Dict[str, RightsEntry] = {}
        self.load_ledger()
        
    def load_ledger(self) -> bool:
        """Load rights ledger from storage"""
        try:
            if self.ledger_path.exists():
                with open(self.ledger_path, 'r') as f:
                    data = json.load(f)
                
                self.entries = {}
                for entry_data in data.get("entries", []):
                    entry = self._deserialize_entry(entry_data)
                    if entry:
                        self.entries[entry.entry_id] = entry
                
                logger.info(f"Loaded {len(self.entries)} rights entries")
                return True
            else:
                logger.info("No existing rights ledger found, starting fresh")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load rights ledger: {e}")
            return False
    
    def save_ledger(self) -> bool:
        """Save rights ledger to storage"""
        try:
            data = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "entries": [self._serialize_entry(entry) for entry in self.entries.values()]
            }
            
            with open(self.ledger_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.entries)} rights entries to ledger")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save rights ledger: {e}")
            return False
    
    def create_rights_entry(self,
                           surface_id: str,
                           title_id: str, 
                           shot_id: str,
                           placement_type: PlacementType,
                           rights_holder: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> RightsEntry:
        """Create new rights entry for placement opportunity"""
        entry_id = str(uuid.uuid4())
        now = datetime.now()
        
        entry = RightsEntry(
            entry_id=entry_id,
            surface_id=surface_id,
            title_id=title_id,
            shot_id=shot_id,
            placement_type=placement_type,
            status=RightsStatus.AVAILABLE,
            rights_holder=rights_holder,
            licensee=None,
            license_start=None,
            license_end=None,
            territory=["worldwide"],  # Default territory
            media_rights=["streaming", "broadcast", "digital"],
            exclusivity=False,
            revenue_share=None,
            placement_fee=None,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        self.entries[entry_id] = entry
        logger.info(f"Created rights entry {entry_id} for surface {surface_id}")
        
        return entry
    
    def reserve_rights(self,
                      entry_id: str,
                      licensee: str,
                      duration_hours: int = 24) -> bool:
        """Reserve placement rights temporarily"""
        if entry_id not in self.entries:
            logger.error(f"Rights entry {entry_id} not found")
            return False
        
        entry = self.entries[entry_id]
        
        if entry.status != RightsStatus.AVAILABLE:
            logger.error(f"Rights {entry_id} not available for reservation")
            return False
        
        entry.status = RightsStatus.RESERVED
        entry.licensee = licensee
        entry.license_start = datetime.now()
        entry.license_end = entry.license_start + timedelta(hours=duration_hours)
        entry.updated_at = datetime.now()
        
        logger.info(f"Reserved rights {entry_id} for {licensee} until {entry.license_end}")
        return True
    
    def license_rights(self,
                      entry_id: str,
                      licensee: str,
                      terms: LicenseTerms) -> bool:
        """License placement rights with specific terms"""
        if entry_id not in self.entries:
            logger.error(f"Rights entry {entry_id} not found")
            return False
        
        entry = self.entries[entry_id]
        
        if entry.status not in [RightsStatus.AVAILABLE, RightsStatus.RESERVED]:
            logger.error(f"Rights {entry_id} cannot be licensed in current status: {entry.status}")
            return False
        
        # Apply license terms
        entry.status = RightsStatus.LICENSED
        entry.licensee = licensee
        entry.license_start = datetime.now()
        entry.license_end = entry.license_start + timedelta(days=terms.duration_months * 30)
        entry.territory = terms.territory
        entry.media_rights = terms.media_rights
        entry.exclusivity = terms.exclusivity
        entry.revenue_share = terms.revenue_share
        entry.placement_fee = terms.minimum_fee
        entry.updated_at = datetime.now()
        
        # Store license terms in metadata
        entry.metadata.update({
            "license_terms": {
                "duration_months": terms.duration_months,
                "territory": terms.territory,
                "media_rights": terms.media_rights,
                "exclusivity": terms.exclusivity,
                "revenue_share": terms.revenue_share,
                "minimum_fee": terms.minimum_fee,
                "usage_restrictions": terms.usage_restrictions,
                "brand_safety_requirements": terms.brand_safety_requirements
            }
        })
        
        logger.info(f"Licensed rights {entry_id} to {licensee} for {terms.duration_months} months")
        return True
    
    def release_rights(self, entry_id: str, reason: str = "manual_release") -> bool:
        """Release placement rights back to available status"""
        if entry_id not in self.entries:
            logger.error(f"Rights entry {entry_id} not found")
            return False
        
        entry = self.entries[entry_id]
        entry.status = RightsStatus.AVAILABLE
        entry.licensee = None
        entry.license_start = None
        entry.license_end = None
        entry.updated_at = datetime.now()
        
        # Log the release reason
        if "release_history" not in entry.metadata:
            entry.metadata["release_history"] = []
        
        entry.metadata["release_history"].append({
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        logger.info(f"Released rights {entry_id}: {reason}")
        return True
    
    def check_expired_licenses(self) -> List[str]:
        """Check for and update expired licenses"""
        expired_entries = []
        now = datetime.now()
        
        for entry_id, entry in self.entries.items():
            if (entry.status == RightsStatus.LICENSED and 
                entry.license_end and 
                now > entry.license_end):
                
                entry.status = RightsStatus.EXPIRED
                entry.updated_at = now
                expired_entries.append(entry_id)
                
                logger.info(f"Rights {entry_id} expired on {entry.license_end}")
        
        return expired_entries
    
    def get_available_rights(self, 
                           title_id: Optional[str] = None,
                           placement_type: Optional[PlacementType] = None) -> List[RightsEntry]:
        """Get available placement rights"""
        available = []
        
        for entry in self.entries.values():
            if entry.status != RightsStatus.AVAILABLE:
                continue
                
            if title_id and entry.title_id != title_id:
                continue
                
            if placement_type and entry.placement_type != placement_type:
                continue
            
            available.append(entry)
        
        return available
    
    def get_licensed_rights(self, licensee: Optional[str] = None) -> List[RightsEntry]:
        """Get currently licensed rights"""
        licensed = []
        
        for entry in self.entries.values():
            if entry.status != RightsStatus.LICENSED:
                continue
                
            if licensee and entry.licensee != licensee:
                continue
            
            licensed.append(entry)
        
        return licensed
    
    def validate_placement_compliance(self, 
                                    entry_id: str,
                                    placement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate placement against license terms"""
        if entry_id not in self.entries:
            return {"valid": False, "error": "Rights entry not found"}
        
        entry = self.entries[entry_id]
        
        if entry.status != RightsStatus.LICENSED:
            return {"valid": False, "error": "Rights not currently licensed"}
        
        # Check license expiration
        if entry.license_end and datetime.now() > entry.license_end:
            return {"valid": False, "error": "License has expired"}
        
        violations = []
        warnings = []
        
        # Check territory compliance
        requested_territory = placement_data.get("territory", ["worldwide"])
        if not set(requested_territory).issubset(set(entry.territory)):
            violations.append("Territory restriction violation")
        
        # Check media rights compliance
        requested_media = placement_data.get("media_rights", ["streaming"])
        if not set(requested_media).issubset(set(entry.media_rights)):
            violations.append("Media rights restriction violation")
        
        # Check exclusivity
        if entry.exclusivity:
            # Would check for other concurrent placements
            pass
        
        # Check brand safety requirements
        license_terms = entry.metadata.get("license_terms", {})
        brand_requirements = license_terms.get("brand_safety_requirements", {})
        
        if brand_requirements:
            # Mock brand safety validation
            placement_content_rating = placement_data.get("content_rating", "unknown")
            required_rating = brand_requirements.get("min_content_rating", "G")
            
            if self._compare_content_ratings(placement_content_rating, required_rating) < 0:
                violations.append(f"Content rating violation: {placement_content_rating} < {required_rating}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "license_valid_until": entry.license_end.isoformat() if entry.license_end else None
        }
    
    def generate_rights_report(self) -> Dict[str, Any]:
        """Generate comprehensive rights report"""
        now = datetime.now()
        
        # Count entries by status
        status_counts = {}
        for status in RightsStatus:
            status_counts[status.value] = sum(
                1 for entry in self.entries.values() if entry.status == status
            )
        
        # Calculate revenue
        total_revenue = sum(
            entry.placement_fee or 0 for entry in self.entries.values()
            if entry.status == RightsStatus.LICENSED
        )
        
        # Active licenses
        active_licenses = [
            entry for entry in self.entries.values()
            if entry.status == RightsStatus.LICENSED and
            (not entry.license_end or entry.license_end > now)
        ]
        
        # Expiring soon (next 30 days)
        expiring_soon = [
            entry for entry in active_licenses
            if entry.license_end and 
            entry.license_end < now + timedelta(days=30)
        ]
        
        report = {
            "generated_at": now.isoformat(),
            "total_entries": len(self.entries),
            "status_breakdown": status_counts,
            "active_licenses": len(active_licenses),
            "total_revenue": total_revenue,
            "expiring_soon": len(expiring_soon),
            "top_licensees": self._get_top_licensees(),
            "popular_placements": self._get_popular_placements(),
            "territory_distribution": self._get_territory_distribution()
        }
        
        return report
    
    def _serialize_entry(self, entry: RightsEntry) -> Dict[str, Any]:
        """Serialize rights entry for storage"""
        data = asdict(entry)
        
        # Convert enums to strings
        data["placement_type"] = entry.placement_type.value
        data["status"] = entry.status.value
        
        # Convert datetime objects to ISO strings
        for field in ["license_start", "license_end", "created_at", "updated_at"]:
            if data[field]:
                data[field] = data[field].isoformat()
        
        return data
    
    def _deserialize_entry(self, data: Dict[str, Any]) -> Optional[RightsEntry]:
        """Deserialize rights entry from storage"""
        try:
            # Convert strings back to enums
            data["placement_type"] = PlacementType(data["placement_type"])
            data["status"] = RightsStatus(data["status"])
            
            # Convert ISO strings back to datetime objects
            for field in ["license_start", "license_end", "created_at", "updated_at"]:
                if data[field]:
                    data[field] = datetime.fromisoformat(data[field])
            
            return RightsEntry(**data)
            
        except Exception as e:
            logger.error(f"Failed to deserialize rights entry: {e}")
            return None
    
    def _compare_content_ratings(self, rating1: str, rating2: str) -> int:
        """Compare content ratings (-1: rating1 < rating2, 0: equal, 1: rating1 > rating2)"""
        ratings_order = ["G", "PG", "PG-13", "R", "NC-17", "unknown"]
        
        try:
            idx1 = ratings_order.index(rating1)
            idx2 = ratings_order.index(rating2)
            return (idx1 > idx2) - (idx1 < idx2)
        except ValueError:
            return 0  # Unknown ratings are considered equal
    
    def _get_top_licensees(self) -> List[Dict[str, Any]]:
        """Get top licensees by number of licenses"""
        licensee_counts = {}
        
        for entry in self.entries.values():
            if entry.licensee:
                licensee_counts[entry.licensee] = licensee_counts.get(entry.licensee, 0) + 1
        
        return sorted(
            [{"licensee": k, "count": v} for k, v in licensee_counts.items()],
            key=lambda x: x["count"], reverse=True
        )[:10]
    
    def _get_popular_placements(self) -> List[Dict[str, Any]]:
        """Get most popular placement types"""
        type_counts = {}
        
        for entry in self.entries.values():
            ptype = entry.placement_type.value
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        return sorted(
            [{"type": k, "count": v} for k, v in type_counts.items()],
            key=lambda x: x["count"], reverse=True
        )
    
    def _get_territory_distribution(self) -> Dict[str, int]:
        """Get distribution of territories"""
        territory_counts = {}
        
        for entry in self.entries.values():
            for territory in entry.territory:
                territory_counts[territory] = territory_counts.get(territory, 0) + 1
        
        return territory_counts

def manage_rights(ledger_path: Optional[Path] = None) -> RightsLedger:
    """
    Convenience function to get rights ledger instance
    
    Args:
        ledger_path: Optional path to ledger file
        
    Returns:
        RightsLedger instance
    """
    return RightsLedger(ledger_path)

# Mock rights management for testing
def mock_rights_management() -> Dict[str, Any]:
    """Generate mock rights management data for CI testing"""
    return {
        "total_entries": 156,
        "available_rights": 89,
        "licensed_rights": 52,
        "expired_rights": 12,
        "total_revenue": 247650.00,
        "top_licensees": [
            {"licensee": "Nike", "active_licenses": 8, "revenue": 45000},
            {"licensee": "Apple", "active_licenses": 6, "revenue": 52000},
            {"licensee": "Coca-Cola", "active_licenses": 5, "revenue": 38500}
        ],
        "placement_types": {
            "logo_overlay": 45,
            "billboard_ad": 38,
            "product_placement": 32,
            "screen_content": 24,
            "virtual_insertion": 17
        }
    }

if __name__ == "__main__":
    # Demo usage
    ledger = RightsLedger()
    
    # Create sample rights entry
    entry = ledger.create_rights_entry(
        surface_id="surf_001",
        title_id="action_movie_2024",
        shot_id="shot_042",
        placement_type=PlacementType.BILLBOARD_AD,
        rights_holder="Studio Productions LLC"
    )
    
    # Create license terms
    terms = LicenseTerms(
        duration_months=6,
        territory=["US", "Canada"],
        media_rights=["streaming", "broadcast"],
        exclusivity=True,
        revenue_share=15.0,
        minimum_fee=25000.0,
        usage_restrictions=["no_competitors"],
        brand_safety_requirements={"min_content_rating": "PG"}
    )
    
    # License the rights
    if ledger.license_rights(entry.entry_id, "Nike Inc.", terms):
        print(f"Licensed rights {entry.entry_id} to Nike Inc.")
    
    # Generate report
    report = ledger.generate_rights_report()
    print(f"Rights report: {report['total_entries']} entries, ${report['total_revenue']} revenue")
    
    # Save ledger
    ledger.save_ledger()