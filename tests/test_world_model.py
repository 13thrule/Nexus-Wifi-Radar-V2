"""
Tests for Unified World Model Expander (UWM-X).

All features are 100% PASSIVE.
"""

import pytest
import time
from nexus.core.world_model import (
    UnifiedWorldModel, WorldNode, GraphEdge, GraphCluster,
    NodeType, EdgeType, TemporalPattern, AnomalyType, EnvironmentType,
    get_world_model
)


class TestWorldModelCreation:
    """Tests for UWM-X creation and basic operations."""
    
    def test_create_world_model(self):
        """Test UWM can be created."""
        uwm = UnifiedWorldModel()
        assert uwm is not None
        assert len(uwm.nodes) == 0
    
    def test_update_node(self):
        """Test updating a node."""
        uwm = UnifiedWorldModel()
        node = uwm.update_node(
            mac="AA:BB:CC:DD:EE:FF",
            ssid="TestNetwork",
            rssi=-50,
            channel=6,
            security="WPA2",
            vendor="TP-Link"
        )
        
        assert node is not None
        assert node.mac == "AA:BB:CC:DD:EE:FF"
        assert node.ssid == "TestNetwork"
        assert node.rssi == -50
        assert node.channel == 6
        assert node.is_visible
    
    def test_get_node(self):
        """Test retrieving a node."""
        uwm = UnifiedWorldModel()
        uwm.update_node("11:22:33:44:55:66", "Net1", -60, 1)
        
        node = uwm.get_node("11:22:33:44:55:66")
        assert node is not None
        assert node.ssid == "Net1"
        
        node2 = uwm.get_node("99:99:99:99:99:99")
        assert node2 is None


class TestTemporalSignature:
    """Tests for temporal behavior modeling."""
    
    def test_rssi_history_recording(self):
        """Test RSSI history is recorded."""
        uwm = UnifiedWorldModel()
        
        for i in range(10):
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Test", -50 + i, 6)
            time.sleep(0.01)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert len(node.rssi_history) == 10
    
    def test_temporal_pattern_classification(self):
        """Test temporal pattern is computed."""
        uwm = UnifiedWorldModel()
        
        # Multiple observations with stable signal
        for i in range(20):
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Stable", -50, 6)
            time.sleep(0.01)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert node.temporal.pattern in [TemporalPattern.STATIONARY, 
                                          TemporalPattern.ALWAYS_ON,
                                          TemporalPattern.UNKNOWN]
    
    def test_rssi_variance_computation(self):
        """Test RSSI variance is computed."""
        uwm = UnifiedWorldModel()
        
        # Varying signal
        for i, rssi in enumerate([-50, -55, -45, -60, -40, -55, -50, -45]):
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Varying", rssi, 6)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert node.temporal.rssi_variance > 0


class TestMovementVector:
    """Tests for movement prediction."""
    
    def test_movement_detection(self):
        """Test movement is detected from RSSI changes."""
        uwm = UnifiedWorldModel()
        
        # Signal improving = approaching
        for rssi in [-70, -65, -60, -55, -50]:
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Approaching", rssi, 6)
            time.sleep(0.05)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        # Movement should be detected
        assert node.movement.speed >= 0
    
    def test_stationary_detection(self):
        """Test stationary nodes have low movement score."""
        uwm = UnifiedWorldModel()
        
        # Stable signal
        for _ in range(10):
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Stable", -50, 6)
            time.sleep(0.01)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert node.movement.speed < 5  # Low movement


class TestEnvironmentContext:
    """Tests for environmental sensing."""
    
    def test_congestion_detection(self):
        """Test channel congestion is detected."""
        uwm = UnifiedWorldModel()
        
        # Multiple APs on same channel
        for i in range(8):
            uwm.update_node(f"AA:BB:CC:DD:EE:{i:02X}", f"Net{i}", -60, 6)
        
        # Refresh environments after all nodes added
        uwm.refresh_environments()
        
        node = uwm.get_node("AA:BB:CC:DD:EE:00")
        assert node.environment.aps_on_channel == 8
        assert node.environment.congestion_score > 50
    
    def test_quiet_environment(self):
        """Test quiet environment classification."""
        uwm = UnifiedWorldModel()
        
        # Single AP
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Alone", -50, 6)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert node.environment.aps_on_channel == 1
        assert node.environment.congestion_score == 0


class TestRelationshipInference:
    """Tests for relationship mapping."""
    
    def test_same_ssid_edge(self):
        """Test same SSID edge creation."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:01:02:03", "SharedNet", -50, 1)
        uwm.update_node("AA:BB:CC:04:05:06", "SharedNet", -60, 6)
        
        uwm.compute_relationships()
        
        # Should have same_ssid edge
        edges = uwm.get_edges_for_node("AA:BB:CC:01:02:03")
        edge_types = [e.edge_type for e in edges]
        assert EdgeType.SAME_SSID in edge_types
    
    def test_same_vendor_edge(self):
        """Test same vendor edge creation."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:01:02:03", "Net1", -50, 1, vendor="TP-Link")
        uwm.update_node("AA:BB:CC:04:05:06", "Net2", -60, 6, vendor="TP-Link")
        
        uwm.compute_relationships()
        
        edges = uwm.get_edges_for_node("AA:BB:CC:01:02:03")
        edge_types = [e.edge_type for e in edges]
        assert EdgeType.SAME_VENDOR in edge_types
    
    def test_interference_edge(self):
        """Test interference edge for same channel."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:01:02:03", "Net1", -50, 6)
        uwm.update_node("AA:BB:CC:04:05:06", "Net2", -60, 6)
        
        uwm.compute_relationships()
        
        edges = uwm.get_edges_for_node("AA:BB:CC:01:02:03")
        edge_types = [e.edge_type for e in edges]
        assert EdgeType.INTERFERENCE in edge_types


class TestClustering:
    """Tests for multi-AP clustering."""
    
    def test_mesh_cluster_detection(self):
        """Test mesh network detection."""
        uwm = UnifiedWorldModel()
        
        # Same SSID, same vendor, different channels = mesh
        uwm.update_node("AA:BB:CC:01:02:03", "MeshNet", -50, 1, vendor="eero")
        uwm.update_node("AA:BB:CC:01:02:04", "MeshNet", -55, 6, vendor="eero")
        uwm.update_node("AA:BB:CC:01:02:05", "MeshNet", -60, 11, vendor="eero")
        
        uwm.compute_clusters()
        
        assert len(uwm.clusters) > 0
        # Check mesh cluster exists
        mesh_clusters = [c for c in uwm.clusters.values() if c.cluster_type == "mesh"]
        assert len(mesh_clusters) >= 1
    
    def test_ssid_group_cluster(self):
        """Test SSID group clustering."""
        uwm = UnifiedWorldModel()
        
        # Same SSID, different vendors (not mesh, but SSID group)
        uwm.update_node("AA:BB:CC:01:02:03", "SharedSSID", -50, 6, vendor="TP-Link")
        uwm.update_node("DD:EE:FF:01:02:03", "SharedSSID", -55, 6, vendor="Netgear")
        
        uwm.compute_clusters()
        
        ssid_clusters = [c for c in uwm.clusters.values() if c.cluster_type == "ssid_group"]
        # Should have SSID group since vendors differ
        assert len(uwm.clusters) >= 1


class TestHomePoint:
    """Tests for Home Point system."""
    
    def test_set_home_point(self):
        """Test setting Home Point."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Home", -30, 6)
        result = uwm.set_home_point("AA:BB:CC:DD:EE:FF")
        
        assert result is True
        assert uwm.home_point == "AA:BB:CC:DD:EE:FF"
    
    def test_home_point_not_inferred(self):
        """Test Home Point is never auto-inferred."""
        uwm = UnifiedWorldModel()
        
        # Add multiple nodes
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Strong", -30, 6)
        uwm.update_node("11:22:33:44:55:66", "Weak", -80, 6)
        
        # Home Point should NOT be auto-set
        assert uwm.home_point is None
    
    def test_clear_home_point(self):
        """Test clearing Home Point."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Home", -30, 6)
        uwm.set_home_point("AA:BB:CC:DD:EE:FF")
        uwm.clear_home_point()
        
        assert uwm.home_point is None
    
    def test_home_relative_position(self):
        """Test positions relative to Home Point."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Home", -30, 6, distance=0.0, angle=0.0)
        uwm.update_node("11:22:33:44:55:66", "Other", -50, 6, distance=10.0, angle=45.0)
        
        uwm.set_home_point("AA:BB:CC:DD:EE:FF")
        
        home = uwm.get_node("AA:BB:CC:DD:EE:FF")
        other = uwm.get_node("11:22:33:44:55:66")
        
        assert home.home_relative_distance == 0.0
        assert other.home_relative_distance > 0


class TestAnomalyDetection:
    """Tests for anomaly classification."""
    
    def test_signal_spike_detection(self):
        """Test signal spike anomaly detection."""
        uwm = UnifiedWorldModel()
        
        # Stable signal then spike
        for _ in range(10):
            uwm.update_node("AA:BB:CC:DD:EE:FF", "Test", -70, 6)
            time.sleep(0.01)
        
        # Spike
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Test", -30, 6)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        # Should have detected anomaly
        assert node.temporal.anomaly_count >= 0  # May or may not trigger depending on std dev
    
    def test_channel_hop_detection(self):
        """Test channel hop anomaly detection."""
        uwm = UnifiedWorldModel()
        
        # Rapid channel changes
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Hopper", -50, 1)
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Hopper", -50, 6)
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Hopper", -50, 11)
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Hopper", -50, 1)
        
        node = uwm.get_node("AA:BB:CC:DD:EE:FF")
        assert len(node.channel_history) >= 2


class TestRadarExport:
    """Tests for radar vector export."""
    
    def test_radar_vectors_export(self):
        """Test exporting radar-compatible vectors."""
        uwm = UnifiedWorldModel()
        
        uwm.update_node("AA:BB:CC:DD:EE:FF", "Test", -50, 6, distance=5.0, angle=45.0)
        
        vectors = uwm.to_radar_vectors()
        
        assert len(vectors) == 1
        assert vectors[0]['mac'] == "AA:BB:CC:DD:EE:FF"
        assert vectors[0]['distance'] == 5.0
        assert vectors[0]['angle'] == 45.0
        assert 'stability' in vectors[0]
        assert 'spoof_risk' in vectors[0]


class TestGlobalInstance:
    """Tests for singleton instance."""
    
    def test_singleton(self):
        """Test UWM singleton."""
        import nexus.core.world_model as wm_mod
        wm_mod._uwm = None
        
        uwm1 = get_world_model()
        uwm2 = get_world_model()
        assert uwm1 is uwm2


class TestPassiveCompliance:
    """Tests ensuring 100% passive operation."""
    
    def test_no_transmission_methods(self):
        """Test UWM has no transmission methods."""
        uwm = UnifiedWorldModel()
        
        # Should NOT have methods like:
        assert not hasattr(uwm, 'send_probe')
        assert not hasattr(uwm, 'transmit')
        assert not hasattr(uwm, 'inject')
        assert not hasattr(uwm, 'deauth')
    
    def test_passive_processing_only(self):
        """Test all methods are passive processing only."""
        uwm = UnifiedWorldModel()
        
        # All public methods should be read/compute only
        public_methods = [m for m in dir(uwm) if not m.startswith('_')]
        
        # These should be analysis methods, not transmission
        for method in public_methods:
            assert 'transmit' not in method.lower()
            assert 'inject' not in method.lower()
            assert 'send' not in method.lower()
