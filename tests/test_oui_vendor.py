"""
Tests for OUI Vendor Intelligence Module (OUI-IM).

Validates:
- Vendor lookup from OUI table
- Randomized MAC detection
- Spoof/rogue risk adjustments
- Cluster scoring
- Offline operation
"""

import pytest
from nexus.core.oui_vendor import (
    OUIVendorIntelligence,
    VendorInfo,
    get_oui_intelligence,
    lookup_vendor,
    get_vendor_name,
    is_randomized_mac,
    OUI_TABLE,
    TYPE_TABLE,
    CONSUMER_VENDORS,
    ENTERPRISE_VENDORS,
    IOT_VENDORS,
    MESH_VENDORS,
    MOBILE_VENDORS,
    ISP_VENDORS,
)


class TestOUITable:
    """Test OUI table structure and contents."""
    
    def test_oui_table_populated(self):
        """OUI table should have entries."""
        assert len(OUI_TABLE) > 0
        assert len(OUI_TABLE) > 100  # Substantial coverage
    
    def test_type_table_matches_oui_table(self):
        """Type table should have same entries as OUI table."""
        assert set(OUI_TABLE.keys()) == set(TYPE_TABLE.keys())
    
    def test_all_prefixes_uppercase(self):
        """All OUI prefixes should be uppercase."""
        for prefix in OUI_TABLE.keys():
            assert prefix == prefix.upper()
    
    def test_all_prefixes_valid_format(self):
        """All OUI prefixes should be valid format."""
        import re
        pattern = re.compile(r'^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$')
        for prefix in OUI_TABLE.keys():
            assert pattern.match(prefix), f"Invalid prefix format: {prefix}"
    
    def test_consumer_vendors_included(self):
        """Consumer vendors should be in table."""
        assert '50:C7:BF' in OUI_TABLE  # TP-Link
        assert '00:14:6C' in OUI_TABLE  # Netgear
        assert '00:06:25' in OUI_TABLE  # Linksys
    
    def test_enterprise_vendors_included(self):
        """Enterprise vendors should be in table."""
        assert '00:00:0C' in OUI_TABLE  # Cisco
        assert '00:0B:86' in OUI_TABLE  # Aruba
        assert '78:8A:20' in OUI_TABLE  # Ubiquiti
    
    def test_iot_vendors_included(self):
        """IoT vendors should be in table."""
        assert '68:54:FD' in OUI_TABLE  # Amazon
        assert '18:B4:30' in OUI_TABLE  # Nest
        assert '00:17:88' in OUI_TABLE  # Philips Hue


class TestVendorInfo:
    """Test VendorInfo dataclass."""
    
    def test_vendor_info_creation(self):
        """VendorInfo should be created correctly."""
        info = VendorInfo(
            name="Test Vendor",
            prefix="AA:BB:CC",
            confidence=90.0,
            is_known=True,
            is_randomized=False,
            vendor_type="consumer"
        )
        assert info.name == "Test Vendor"
        assert info.confidence == 90.0
        assert info.is_known is True
    
    def test_vendor_info_to_dict(self):
        """VendorInfo should convert to dict."""
        info = VendorInfo(
            name="Test",
            prefix="AA:BB:CC",
            confidence=100.0,
            is_known=True,
            is_randomized=False,
            vendor_type="enterprise"
        )
        d = info.to_dict()
        assert d['name'] == "Test"
        assert d['vendor_type'] == "enterprise"


class TestOUIVendorIntelligence:
    """Test OUI Vendor Intelligence Module."""
    
    @pytest.fixture
    def oui_im(self):
        """Create fresh OUI-IM instance."""
        return OUIVendorIntelligence()
    
    def test_lookup_known_vendor(self, oui_im):
        """Should find known vendor."""
        info = oui_im.lookup("00:14:6C:11:22:33")  # Netgear - unique prefix
        assert info.name == "Netgear"
        assert info.is_known is True
        assert info.confidence == 100.0
    
    def test_lookup_unknown_vendor(self, oui_im):
        """Should handle unknown vendor."""
        info = oui_im.lookup("FF:FF:FF:11:22:33")
        assert info.name == "Unknown"
        assert info.is_known is False
        assert info.confidence == 0.0
    
    def test_lookup_normalizes_mac(self, oui_im):
        """Should normalize MAC formats."""
        # Lowercase
        info1 = oui_im.lookup("00:14:6c:11:22:33")
        assert info1.name == "Netgear"
        
        # Dashes
        info2 = oui_im.lookup("00-14-6C-11-22-33")
        assert info2.name == "Netgear"
    
    def test_lookup_caches_results(self, oui_im):
        """Should cache lookup results."""
        mac = "00:14:6C:AA:BB:CC"
        info1 = oui_im.lookup(mac)
        info2 = oui_im.lookup(mac)
        assert info1 is info2  # Same object from cache
    
    def test_vendor_type_consumer(self, oui_im):
        """Should identify consumer vendors."""
        info = oui_im.lookup("00:14:6C:11:22:33")  # Netgear
        assert info.vendor_type == "consumer"
    
    def test_vendor_type_enterprise(self, oui_im):
        """Should identify enterprise vendors."""
        info = oui_im.lookup("00:00:0C:11:22:33")  # Cisco
        assert info.vendor_type == "enterprise"
    
    def test_vendor_type_iot(self, oui_im):
        """Should identify IoT vendors."""
        info = oui_im.lookup("68:54:FD:11:22:33")  # Amazon
        assert info.vendor_type == "iot"
    
    def test_vendor_type_mesh(self, oui_im):
        """Should identify mesh vendors."""
        info = oui_im.lookup("E4:F0:42:11:22:33")  # eero
        assert info.vendor_type == "mesh"


class TestRandomizedMACDetection:
    """Test randomized MAC detection."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_detect_locally_administered_mac(self, oui_im):
        """Should detect locally administered bit."""
        # Locally administered bit set (0x02)
        assert oui_im._is_randomized_mac("02:11:22:33:44:55") is True
        assert oui_im._is_randomized_mac("06:11:22:33:44:55") is True
        assert oui_im._is_randomized_mac("0A:11:22:33:44:55") is True
        assert oui_im._is_randomized_mac("0E:11:22:33:44:55") is True
    
    def test_detect_randomization_patterns(self, oui_im):
        """Should detect common randomization patterns."""
        assert oui_im._is_randomized_mac("F2:11:22:33:44:55") is True
        assert oui_im._is_randomized_mac("E6:11:22:33:44:55") is True
        assert oui_im._is_randomized_mac("DA:11:22:33:44:55") is True
    
    def test_real_vendor_not_randomized(self, oui_im):
        """Real vendor MACs should not be flagged as randomized."""
        # TP-Link - known vendor
        info = oui_im.lookup("50:C7:BF:11:22:33")
        assert info.is_randomized is False
        
        # Cisco - known vendor
        info = oui_im.lookup("00:00:0C:11:22:33")
        assert info.is_randomized is False
    
    def test_randomized_reduces_confidence(self, oui_im):
        """Randomized MAC should reduce confidence even if prefix matches."""
        # Create a MAC with locally administered bit that happens to match a prefix
        info = oui_im.lookup("02:C7:BF:11:22:33")
        assert info.is_randomized is True
        # Confidence reduced for randomized
        assert info.confidence < 100.0


class TestSpoofRiskAdjustment:
    """Test spoof risk adjustment calculations."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_unknown_vendor_hidden_strong_signal(self, oui_im):
        """Unknown vendor with hidden SSID and strong signal should be suspicious."""
        adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac="FF:FF:FF:11:22:33",
            is_hidden=True,
            rssi=-40
        )
        assert adjustment > 20.0
    
    def test_vendor_mismatch(self, oui_im):
        """Vendor mismatch should increase spoof risk."""
        adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac="50:C7:BF:11:22:33",  # TP-Link
            claimed_vendor="Cisco",
            rssi=-70
        )
        assert adjustment > 10.0
    
    def test_randomized_mac_hidden(self, oui_im):
        """Randomized MAC with hidden SSID should be suspicious."""
        adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac="02:11:22:33:44:55",
            is_hidden=True,
            rssi=-70
        )
        assert adjustment > 15.0
    
    def test_known_vendor_normal_signal(self, oui_im):
        """Known vendor with normal signal should have minimal adjustment."""
        adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac="50:C7:BF:11:22:33",  # TP-Link
            is_hidden=False,
            rssi=-70
        )
        assert adjustment == 0.0
    
    def test_adjustment_capped(self, oui_im):
        """Adjustment should be capped at 50."""
        adjustment = oui_im.calculate_spoof_risk_adjustment(
            mac="FF:FF:FF:11:22:33",
            claimed_vendor="Cisco",
            is_hidden=True,
            rssi=-30
        )
        assert adjustment <= 50.0


class TestRogueRiskAdjustment:
    """Test rogue risk adjustment calculations."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_unknown_hidden_strong_signal(self, oui_im):
        """Unknown vendor with hidden SSID and strong signal = rogue candidate."""
        adjustment = oui_im.calculate_rogue_risk_adjustment(
            mac="FF:FF:FF:11:22:33",
            is_hidden=True,
            rssi=-40
        )
        assert adjustment >= 30.0
    
    def test_randomized_mac_infrastructure(self, oui_im):
        """Randomized MAC on infrastructure should increase rogue risk."""
        adjustment = oui_im.calculate_rogue_risk_adjustment(
            mac="02:11:22:33:44:55",
            is_hidden=False,
            rssi=-70
        )
        assert adjustment >= 15.0
    
    def test_unknown_5ghz_backhaul(self, oui_im):
        """Unknown vendor on 5GHz backhaul channel should be suspicious."""
        adjustment = oui_im.calculate_rogue_risk_adjustment(
            mac="FF:FF:FF:11:22:33",
            is_hidden=False,
            rssi=-70,
            channel=149
        )
        assert adjustment >= 10.0
    
    def test_known_vendor_minimal_risk(self, oui_im):
        """Known vendor should have minimal rogue risk adjustment."""
        adjustment = oui_im.calculate_rogue_risk_adjustment(
            mac="50:C7:BF:11:22:33",  # TP-Link
            is_hidden=False,
            rssi=-70,
            channel=6
        )
        assert adjustment == 0.0


class TestClusterScoreAdjustment:
    """Test cluster score adjustment calculations."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_matching_vendor_bonus(self, oui_im):
        """Matching vendor should boost cluster score."""
        adjustment = oui_im.calculate_cluster_score_adjustment(
            mac="00:14:6C:11:22:33",  # Netgear
            cluster_vendor="Netgear"
        )
        assert adjustment > 0.0
    
    def test_unknown_vendor_penalty(self, oui_im):
        """Unknown vendor should reduce cluster confidence."""
        adjustment = oui_im.calculate_cluster_score_adjustment(
            mac="FF:FF:FF:11:22:33",
            cluster_vendor="TP-Link"
        )
        assert adjustment < 0.0
    
    def test_different_mesh_vendors_suspicious(self, oui_im):
        """Different mesh vendors in cluster should be suspicious."""
        adjustment = oui_im.calculate_cluster_score_adjustment(
            mac="E4:F0:42:11:22:33",  # eero (mesh)
            cluster_vendor="Google Nest"
        )
        assert adjustment < 0.0


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_oui_intelligence_singleton(self):
        """Should return same instance."""
        im1 = get_oui_intelligence()
        im2 = get_oui_intelligence()
        assert im1 is im2
    
    def test_lookup_vendor_function(self):
        """lookup_vendor should work."""
        info = lookup_vendor("00:14:6C:11:22:33")
        assert info.name == "Netgear"
    
    def test_get_vendor_name_function(self):
        """get_vendor_name should work."""
        name = get_vendor_name("00:00:0C:11:22:33")
        assert name == "Cisco"
    
    def test_is_randomized_mac_function(self):
        """is_randomized_mac should work."""
        assert is_randomized_mac("02:11:22:33:44:55") is True
        assert is_randomized_mac("50:C7:BF:11:22:33") is False


class TestStatistics:
    """Test statistics and utility functions."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_get_statistics(self, oui_im):
        """Should return statistics dict."""
        stats = oui_im.get_statistics()
        assert 'total_ouis' in stats
        assert 'consumer_count' in stats
        assert 'enterprise_count' in stats
        assert 'cache_size' in stats
        assert stats['total_ouis'] > 100
    
    def test_clear_cache(self, oui_im):
        """Should clear lookup cache."""
        oui_im.lookup("50:C7:BF:11:22:33")
        assert len(oui_im.cache) > 0
        oui_im.clear_cache()
        assert len(oui_im.cache) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def oui_im(self):
        return OUIVendorIntelligence()
    
    def test_empty_mac(self, oui_im):
        """Should handle empty MAC gracefully."""
        info = oui_im.lookup("")
        assert info.name == "Unknown"
        assert info.is_known is False
    
    def test_short_mac(self, oui_im):
        """Should handle short MAC."""
        info = oui_im.lookup("AA:BB")
        assert info.name == "Unknown"
    
    def test_invalid_characters(self, oui_im):
        """Should handle invalid characters."""
        info = oui_im.lookup("GG:HH:II:JJ:KK:LL")
        assert info.name == "Unknown"
    
    def test_mixed_case(self, oui_im):
        """Should handle mixed case."""
        info = oui_im.lookup("00:14:6c:Aa:Bb:Cc")
        assert info.name == "Netgear"
    
    def test_multicast_mac(self, oui_im):
        """Should handle multicast MACs."""
        # Multicast bit set
        info = oui_im.lookup("01:00:5E:11:22:33")
        assert info is not None


class TestOfflineOperation:
    """Verify 100% offline operation."""
    
    def test_no_network_imports(self):
        """Module should not import networking libraries."""
        import nexus.core.oui_vendor as oui_module
        import sys
        
        # Check module doesn't import networking
        module_imports = dir(oui_module)
        assert 'requests' not in sys.modules or 'nexus.core.oui_vendor' not in str(sys.modules.get('requests'))
        assert 'urllib' not in module_imports
        assert 'http' not in module_imports
    
    def test_static_data_loaded(self):
        """OUI data should be loaded at module import."""
        from nexus.core.oui_vendor import OUI_TABLE
        assert len(OUI_TABLE) > 0
    
    def test_lookup_no_side_effects(self):
        """Lookup should have no side effects beyond caching."""
        oui_im = OUIVendorIntelligence()
        initial_table_size = len(oui_im.oui_table)
        
        oui_im.lookup("50:C7:BF:11:22:33")
        oui_im.lookup("FF:FF:FF:11:22:33")
        
        assert len(oui_im.oui_table) == initial_table_size
