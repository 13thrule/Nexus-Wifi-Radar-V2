"""
Tests for Hidden Network Classification Engine (HNCE).

All features are 100% PASSIVE.
"""

import pytest
from nexus.core.hidden_classifier import (
    HiddenNetworkClassifier, HiddenNetworkProfile, HiddenCluster,
    HiddenNetworkType, RogueRisk, ClusterType,
    get_hidden_classifier, MESH_VENDOR_OUIS, ENTERPRISE_VENDOR_OUIS
)


class TestHNCECreation:
    """Tests for HNCE creation and basic operations."""
    
    def test_create_classifier(self):
        """Test HNCE can be created."""
        hnce = HiddenNetworkClassifier()
        assert hnce is not None
        assert len(hnce.profiles) == 0
    
    def test_record_hidden_network(self):
        """Test recording a hidden network."""
        hnce = HiddenNetworkClassifier()
        profile = hnce.record_hidden_network(
            bssid="AA:BB:CC:DD:EE:FF",
            channel=6,
            rssi=-50,
            security="WPA2",
            vendor="Unknown"
        )
        
        assert profile is not None
        assert profile.bssid == "AA:BB:CC:DD:EE:FF"
        assert profile.channel == 6
        assert profile.rssi == -50
        assert profile.oui == "AA:BB:CC"
    
    def test_get_profile(self):
        """Test retrieving a profile."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("11:22:33:44:55:66", 6, -60)
        
        profile = hnce.get_profile("11:22:33:44:55:66")
        assert profile is not None
        assert profile.channel == 6
        
        profile2 = hnce.get_profile("99:99:99:99:99:99")
        assert profile2 is None


class TestOUIConsistency:
    """Tests for OUI consistency scoring."""
    
    def test_single_oui_score(self):
        """Test OUI score for single device."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        assert profile.oui_consistency_score == 50.0  # Single device baseline
    
    def test_multiple_same_oui_score(self):
        """Test OUI score for multiple devices with same OUI."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 11, -55)
        hnce.record_hidden_network("AA:BB:CC:77:88:99", 1, -60)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        assert profile.oui_consistency_score > 50.0  # Multiple same OUI = higher score
    
    def test_mesh_oui_bonus(self):
        """Test OUI score bonus for mesh vendors."""
        hnce = HiddenNetworkClassifier()
        # Use known mesh OUI
        mesh_oui = list(MESH_VENDOR_OUIS)[0]
        bssid = f"{mesh_oui}:11:22:33"
        hnce.record_hidden_network(bssid, 6, -50)
        hnce.analyze()
        
        profile = hnce.get_profile(bssid)
        # Should get bonus for mesh vendor
        assert profile.oui_consistency_score >= 70.0


class TestChannelCoherence:
    """Tests for channel coherence scoring."""
    
    def test_same_channel_coherence(self):
        """Test coherence when all on same channel."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 6, -55)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        # Same OUI, same channel = high coherence
        assert profile.channel_coherence_score > 70.0
    
    def test_different_channel_coherence(self):
        """Test coherence with varied channels."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 1, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 6, -55)
        hnce.record_hidden_network("AA:BB:CC:77:88:99", 11, -60)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        # Different channels = lower coherence
        assert profile.channel_coherence_score < 80.0


class TestSignalGrouping:
    """Tests for signal grouping scoring."""
    
    def test_similar_signals_grouping(self):
        """Test grouping when signals are similar."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 6, -52)
        hnce.record_hidden_network("AA:BB:CC:77:88:99", 6, -48)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        # Similar RSSI values = high grouping score
        assert profile.signal_grouping_score > 60.0
    
    def test_varied_signals_grouping(self):
        """Test grouping when signals vary."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -30)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 6, -70)
        hnce.record_hidden_network("AA:BB:CC:77:88:99", 6, -90)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        # High RSSI variance = lower grouping score
        assert profile.signal_grouping_score < 80.0


class TestRogueLikelihood:
    """Tests for rogue likelihood scoring."""
    
    def test_low_rogue_score_known_vendor(self):
        """Test low rogue score for known mesh vendor."""
        hnce = HiddenNetworkClassifier()
        mesh_oui = list(MESH_VENDOR_OUIS)[0]
        bssid = f"{mesh_oui}:11:22:33"
        hnce.record_hidden_network(bssid, 6, -60, security="WPA2")
        hnce.analyze()
        
        profile = hnce.get_profile(bssid)
        assert profile.rogue_likelihood_score < 50
    
    def test_high_rogue_score_unknown_strong_signal(self):
        """Test high rogue score for unknown vendor with strong signal."""
        hnce = HiddenNetworkClassifier()
        # Unknown OUI with very strong signal
        hnce.record_hidden_network("FF:FF:FF:11:22:33", 6, -35, security="Open")
        hnce.analyze()
        
        profile = hnce.get_profile("FF:FF:FF:11:22:33")
        # Should have elevated rogue score and be flagged as rogue candidate
        assert profile.rogue_likelihood_score > 30
        assert profile.is_rogue_candidate
    
    def test_rogue_candidate_flagging(self):
        """Test rogue candidate is flagged."""
        hnce = HiddenNetworkClassifier()
        # Suspicious: unknown vendor, open security, strong signal
        hnce.record_hidden_network("FF:FF:FF:11:22:33", 6, -30, security="Open")
        hnce.analyze()
        
        profile = hnce.get_profile("FF:FF:FF:11:22:33")
        assert profile.is_rogue_candidate


class TestNetworkClassification:
    """Tests for network classification."""
    
    def test_classify_mesh_node(self):
        """Test mesh node classification."""
        hnce = HiddenNetworkClassifier()
        mesh_oui = list(MESH_VENDOR_OUIS)[0]
        # Multiple nodes with same mesh OUI
        hnce.record_hidden_network(f"{mesh_oui}:11:22:33", 6, -50)
        hnce.record_hidden_network(f"{mesh_oui}:44:55:66", 11, -55)
        hnce.analyze()
        
        profile = hnce.get_profile(f"{mesh_oui}:11:22:33")
        assert profile.network_type == HiddenNetworkType.MESH_NODE
    
    def test_classify_enterprise_ap(self):
        """Test enterprise AP classification."""
        hnce = HiddenNetworkClassifier()
        # Use HPE/Aruba OUI which is enterprise-only, not in mesh list
        enterprise_oui = "00:04:96"  # HPE/Aruba - only in enterprise list
        hnce.record_hidden_network(f"{enterprise_oui}:11:22:33", 6, -50)
        hnce.analyze()
        
        profile = hnce.get_profile(f"{enterprise_oui}:11:22:33")
        assert profile.network_type == HiddenNetworkType.ENTERPRISE_AP
    
    def test_classify_backhaul(self):
        """Test backhaul link classification."""
        hnce = HiddenNetworkClassifier()
        # Multiple on 5GHz backhaul channel
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 149, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 149, -55)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        assert profile.network_type == HiddenNetworkType.BACKHAUL_LINK


class TestClustering:
    """Tests for hidden network clustering."""
    
    def test_cluster_by_oui(self):
        """Test clustering by OUI."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.record_hidden_network("AA:BB:CC:44:55:66", 11, -55)
        hnce.record_hidden_network("DD:EE:FF:11:22:33", 6, -60)
        hnce.analyze()
        
        # Should have 2 clusters: one with 2 members (same OUI), one single
        assert len(hnce.clusters) == 2
    
    def test_mesh_cluster_detection(self):
        """Test mesh cluster detection."""
        hnce = HiddenNetworkClassifier()
        mesh_oui = list(MESH_VENDOR_OUIS)[0]
        hnce.record_hidden_network(f"{mesh_oui}:11:22:33", 6, -50)
        hnce.record_hidden_network(f"{mesh_oui}:44:55:66", 11, -55)
        hnce.record_hidden_network(f"{mesh_oui}:77:88:99", 1, -60)
        hnce.analyze()
        
        mesh_clusters = hnce.get_clusters_by_type(ClusterType.MESH_CLUSTER)
        assert len(mesh_clusters) >= 1
    
    def test_single_device_cluster(self):
        """Test single device cluster."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.analyze()
        
        single_clusters = hnce.get_clusters_by_type(ClusterType.SINGLE_DEVICE)
        assert len(single_clusters) == 1


class TestVisibleCorrelation:
    """Tests for correlation with visible networks."""
    
    def test_correlate_with_visible(self):
        """Test correlation with visible networks."""
        hnce = HiddenNetworkClassifier()
        
        # Record visible network
        hnce.record_visible_network(
            bssid="AA:BB:CC:11:11:11",
            ssid="MyNetwork",
            channel=6,
            rssi=-45,
            vendor="TP-Link"
        )
        
        # Record hidden network with same OUI and channel
        hnce.record_hidden_network("AA:BB:CC:22:22:22", 6, -50)
        hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:22:22:22")
        # Should be correlated and classified as guest isolated
        assert len(profile.related_bssids) > 0 or profile.network_type != HiddenNetworkType.UNKNOWN


class TestSpoofDetection:
    """Tests for spoof candidate detection."""
    
    def test_spoof_pattern_detection(self):
        """Test spoof pattern is detected."""
        hnce = HiddenNetworkClassifier()
        
        # Record visible network
        hnce.record_visible_network(
            bssid="AA:BB:CC:11:22:33",
            ssid="TargetNetwork",
            channel=6,
            rssi=-50,
            vendor="TP-Link"
        )
        
        # Record hidden network that mimics it (same channel, similar RSSI, different OUI)
        hnce.record_hidden_network("DD:EE:FF:11:22:33", 6, -52)
        hnce.analyze()
        
        profile = hnce.get_profile("DD:EE:FF:11:22:33")
        # Should be flagged as spoof candidate
        assert profile.is_spoof_candidate


class TestAnalysisSummary:
    """Tests for analysis summary."""
    
    def test_summary_generation(self):
        """Test summary is generated correctly."""
        hnce = HiddenNetworkClassifier()
        mesh_oui = list(MESH_VENDOR_OUIS)[0]
        
        hnce.record_hidden_network(f"{mesh_oui}:11:22:33", 6, -50)
        hnce.record_hidden_network(f"{mesh_oui}:44:55:66", 11, -55)
        hnce.record_hidden_network("FF:FF:FF:11:22:33", 6, -30, security="Open")
        
        summary = hnce.get_summary()
        
        assert summary['hidden_count'] == 3
        assert 'cluster_count' in summary
        assert 'mesh_count' in summary
        assert 'rogue_candidates' in summary


class TestGlobalSingleton:
    """Tests for global singleton."""
    
    def test_singleton(self):
        """Test HNCE singleton."""
        import nexus.core.hidden_classifier as hc_mod
        hc_mod._hnce = None
        
        hnce1 = get_hidden_classifier()
        hnce2 = get_hidden_classifier()
        assert hnce1 is hnce2


class TestPassiveCompliance:
    """Tests ensuring 100% passive operation."""
    
    def test_no_transmission_methods(self):
        """Test HNCE has no transmission methods."""
        hnce = HiddenNetworkClassifier()
        
        assert not hasattr(hnce, 'send_probe')
        assert not hasattr(hnce, 'transmit')
        assert not hasattr(hnce, 'inject')
        assert not hasattr(hnce, 'deauth')
    
    def test_passive_processing_only(self):
        """Test all methods are passive processing only."""
        hnce = HiddenNetworkClassifier()
        
        public_methods = [m for m in dir(hnce) if not m.startswith('_')]
        
        for method in public_methods:
            assert 'transmit' not in method.lower()
            assert 'inject' not in method.lower()
            assert 'send' not in method.lower()


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_single_hidden_ap(self):
        """Test single hidden AP is handled."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        result = hnce.analyze()
        
        assert result.hidden_count == 1
        assert result.cluster_count == 1
    
    def test_empty_analysis(self):
        """Test empty analysis returns valid result."""
        hnce = HiddenNetworkClassifier()
        result = hnce.analyze()
        
        assert result.hidden_count == 0
        assert result.cluster_count == 0
    
    def test_very_weak_signal(self):
        """Test very weak signals are handled."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -95)
        result = hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        assert profile is not None
        assert profile.rssi == -95
    
    def test_dfs_channel(self):
        """Test DFS channel handling."""
        hnce = HiddenNetworkClassifier()
        # DFS channel
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 100, -50)
        result = hnce.analyze()
        
        profile = hnce.get_profile("AA:BB:CC:11:22:33")
        assert profile is not None
        assert profile.channel == 100
    
    def test_clear(self):
        """Test clear functionality."""
        hnce = HiddenNetworkClassifier()
        hnce.record_hidden_network("AA:BB:CC:11:22:33", 6, -50)
        hnce.analyze()
        
        hnce.clear()
        
        assert len(hnce.profiles) == 0
        assert len(hnce.clusters) == 0
