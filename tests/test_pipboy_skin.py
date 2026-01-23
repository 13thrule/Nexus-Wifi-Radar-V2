"""
Tests for Pip-Boy UI Skin Plugin

Validates the Pip-Boy skin system:
- Color palette definitions
- Theme dict compatibility
- Font configuration
- Animation system
- TTK style configuration
- Helper widget creation
- Apply/revert functionality
- 100% offline operation
"""

import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk


class TestPipBoyImports:
    """Test that all Pip-Boy skin components can be imported."""
    
    def test_import_pipboy_module(self):
        """Test importing the pipboy module."""
        from nexus.ui.skins import pipboy
        assert pipboy is not None
    
    def test_import_pipboy_skin_class(self):
        """Test importing PipBoySkin class."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert PipBoySkin is not None
    
    def test_import_get_pipboy_skin(self):
        """Test importing get_pipboy_skin function."""
        from nexus.ui.skins.pipboy import get_pipboy_skin
        assert callable(get_pipboy_skin)
    
    def test_import_pipboy_theme(self):
        """Test importing PIPBOY_THEME dict."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME
        assert isinstance(PIPBOY_THEME, dict)
    
    def test_import_from_skins_package(self):
        """Test importing from the skins package."""
        from nexus.ui.skins import PipBoySkin, get_pipboy_skin, PIPBOY_THEME
        assert PipBoySkin is not None
        assert callable(get_pipboy_skin)
        assert isinstance(PIPBOY_THEME, dict)


class TestPipBoyPalette:
    """Test the Pip-Boy color palette."""
    
    def test_palette_class_exists(self):
        """Test PipBoyPalette class exists."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        assert PipBoyPalette is not None
    
    def test_green_primary_color(self):
        """Test primary green color defined."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        assert hasattr(PipBoyPalette, 'GREEN_PRIMARY')
        assert PipBoyPalette.GREEN_PRIMARY.startswith('#')
    
    def test_green_bright_color(self):
        """Test bright green color defined."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        assert hasattr(PipBoyPalette, 'GREEN_BRIGHT')
        assert PipBoyPalette.GREEN_BRIGHT.startswith('#')
    
    def test_amber_color(self):
        """Test amber accent color defined."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        assert hasattr(PipBoyPalette, 'AMBER_BRIGHT')
        assert PipBoyPalette.AMBER_BRIGHT.startswith('#')
    
    def test_background_colors(self):
        """Test background colors defined."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        assert hasattr(PipBoyPalette, 'BG_BLACK')
        assert hasattr(PipBoyPalette, 'BG_DARK')
    
    def test_primary_colors_are_valid_hex(self):
        """Test primary color values are valid hex codes."""
        from nexus.ui.skins.pipboy import PipBoyPalette
        # Test primary colors (exclude ones with alpha)
        primary_colors = [
            'GREEN_BRIGHT', 'GREEN_PRIMARY', 'GREEN_MEDIUM', 'GREEN_DIM',
            'GREEN_DARK', 'GREEN_DARKER', 'AMBER_BRIGHT', 'AMBER_PRIMARY',
            'BG_BLACK', 'BG_DARK', 'BG_PANEL', 'BG_CARD'
        ]
        for color_name in primary_colors:
            if hasattr(PipBoyPalette, color_name):
                color = getattr(PipBoyPalette, color_name)
                assert color.startswith('#'), f"{color_name} should be hex color"
                assert len(color) == 7, f"{color_name} should be #RRGGBB format"


class TestPipBoyTheme:
    """Test the PIPBOY_THEME dict compatibility."""
    
    def test_theme_has_core_keys(self):
        """Test theme has core color keys for app.py compatibility."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME
        core_keys = [
            'name', 'bg_main', 'bg_panel', 'text_primary', 'text_secondary',
            'text_accent', 'radar_bg'
        ]
        for key in core_keys:
            assert key in PIPBOY_THEME, f"Missing core key: {key}"
    
    def test_theme_name_is_string(self):
        """Test theme name is a string."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME
        assert isinstance(PIPBOY_THEME['name'], str)
        assert len(PIPBOY_THEME['name']) > 0
    
    def test_theme_background_colors_are_hex(self):
        """Test background colors are hex strings."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME
        bg_keys = ['bg_main', 'bg_panel', 'radar_bg']
        for key in bg_keys:
            value = PIPBOY_THEME[key]
            assert isinstance(value, str), f"{key} should be string"
            assert value.startswith('#'), f"{key} should be hex color"
    
    def test_theme_has_crt_settings(self):
        """Test theme has CRT effect settings."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME
        crt_keys = ['crt_enabled', 'scanlines', 'flicker', 'glow']
        for key in crt_keys:
            assert key in PIPBOY_THEME, f"Missing CRT key: {key}"
    
    def test_theme_uses_palette_colors(self):
        """Test theme uses colors from the palette."""
        from nexus.ui.skins.pipboy import PIPBOY_THEME, PipBoyPalette
        # text_primary should match palette
        assert PIPBOY_THEME['text_primary'] == PipBoyPalette.GREEN_PRIMARY


class TestPipBoyFonts:
    """Test the Pip-Boy font configuration."""
    
    def test_fonts_class_exists(self):
        """Test PipBoyFonts class exists."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        assert PipBoyFonts is not None
    
    def test_terminal_fonts_list(self):
        """Test terminal fonts list defined."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        assert hasattr(PipBoyFonts, 'TERMINAL_FONTS')
        fonts = PipBoyFonts.TERMINAL_FONTS
        assert isinstance(fonts, list)
        assert len(fonts) > 0
    
    def test_header_fonts_list(self):
        """Test header fonts list defined."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        assert hasattr(PipBoyFonts, 'HEADER_FONTS')
        fonts = PipBoyFonts.HEADER_FONTS
        assert isinstance(fonts, list)
        assert len(fonts) > 0
    
    def test_get_terminal_font_method(self):
        """Test get_terminal_font method."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        font = PipBoyFonts.get_terminal_font(10)
        assert isinstance(font, tuple)
        assert len(font) >= 2
        assert isinstance(font[1], int)
    
    def test_get_header_font_method(self):
        """Test get_header_font method."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        font = PipBoyFonts.get_header_font(12)
        assert isinstance(font, tuple)
        assert len(font) >= 2
    
    def test_font_fallback_strategy(self):
        """Test fonts have fallback strategy."""
        from nexus.ui.skins.pipboy import PipBoyFonts
        # Should have multiple fonts as fallbacks
        assert len(PipBoyFonts.TERMINAL_FONTS) >= 3


class TestAnimationState:
    """Test the animation state dataclass."""
    
    def test_animation_state_exists(self):
        """Test AnimationState class exists."""
        from nexus.ui.skins.pipboy import AnimationState
        assert AnimationState is not None
    
    def test_animation_state_defaults(self):
        """Test AnimationState has sensible defaults."""
        from nexus.ui.skins.pipboy import AnimationState
        state = AnimationState()
        assert hasattr(state, 'scanline_offset')
        assert hasattr(state, 'glow_phase')
        assert hasattr(state, 'flicker_phase')
        assert hasattr(state, 'radar_sweep_angle')
    
    def test_animation_state_values(self):
        """Test AnimationState default values."""
        from nexus.ui.skins.pipboy import AnimationState
        state = AnimationState()
        assert state.scanline_offset == 0.0
        assert state.glow_phase == 0.0


class TestCRTAnimator:
    """Test the CRT animation controller."""
    
    def test_animator_class_exists(self):
        """Test CRTAnimator class exists."""
        from nexus.ui.skins.pipboy import CRTAnimator
        assert CRTAnimator is not None
    
    def test_animator_requires_root(self):
        """Test animator requires root window."""
        from nexus.ui.skins.pipboy import CRTAnimator
        import inspect
        sig = inspect.signature(CRTAnimator.__init__)
        params = list(sig.parameters.keys())
        assert 'root' in params
    
    def test_animator_has_start_stop(self):
        """Test animator has start/stop methods."""
        from nexus.ui.skins.pipboy import CRTAnimator
        assert hasattr(CRTAnimator, 'start')
        assert hasattr(CRTAnimator, 'stop')
        assert callable(CRTAnimator.start)
        assert callable(CRTAnimator.stop)


class TestPipBoySkinClass:
    """Test the main PipBoySkin class."""
    
    def test_skin_requires_root(self):
        """Test PipBoySkin requires root window."""
        from nexus.ui.skins.pipboy import PipBoySkin
        import inspect
        sig = inspect.signature(PipBoySkin.__init__)
        params = list(sig.parameters.keys())
        assert 'root' in params
    
    def test_skin_has_apply_method(self):
        """Test skin has apply method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'apply')
        assert callable(PipBoySkin.apply)
    
    def test_skin_has_revert_method(self):
        """Test skin has revert method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'revert')
        assert callable(PipBoySkin.revert)
    
    def test_skin_has_get_theme_method(self):
        """Test skin has get_theme method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'get_theme')
        assert callable(PipBoySkin.get_theme)


class TestSkinSingleton:
    """Test the singleton accessor function."""
    
    def test_get_pipboy_skin_callable(self):
        """Test get_pipboy_skin is callable."""
        from nexus.ui.skins.pipboy import get_pipboy_skin
        assert callable(get_pipboy_skin)
    
    def test_get_pipboy_skin_without_root_returns_none(self):
        """Test get_pipboy_skin returns None without root."""
        from nexus.ui.skins import pipboy
        # Reset singleton for test
        pipboy._pipboy_skin = None
        skin = pipboy.get_pipboy_skin()
        assert skin is None
    
    def test_get_pipboy_theme_function(self):
        """Test get_pipboy_theme function."""
        from nexus.ui.skins.pipboy import get_pipboy_theme, PIPBOY_THEME
        theme = get_pipboy_theme()
        assert isinstance(theme, dict)
        assert theme == PIPBOY_THEME


class TestPipBoyDecorations:
    """Test the decorative ASCII elements."""
    
    def test_decorations_class_exists(self):
        """Test PipBoyDecorations class exists."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        assert PipBoyDecorations is not None
    
    def test_vault_tec_header_exists(self):
        """Test Vault-Tec header ASCII art defined."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        assert hasattr(PipBoyDecorations, 'VAULT_TEC_HEADER')
        assert isinstance(PipBoyDecorations.VAULT_TEC_HEADER, str)
    
    def test_box_drawing_chars(self):
        """Test box drawing characters defined."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        assert hasattr(PipBoyDecorations, 'BOX_H')
        assert hasattr(PipBoyDecorations, 'BOX_V')
        assert hasattr(PipBoyDecorations, 'BOX_TL')
        assert hasattr(PipBoyDecorations, 'BOX_BR')
    
    def test_progress_bar_chars(self):
        """Test progress bar characters defined."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        assert hasattr(PipBoyDecorations, 'PROG_FULL')
        assert hasattr(PipBoyDecorations, 'PROG_EMPTY')
    
    def test_make_header_method(self):
        """Test make_header method."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        header = PipBoyDecorations.make_header("TEST", 30)
        assert isinstance(header, str)
        assert "TEST" in header
    
    def test_make_progress_bar_method(self):
        """Test make_progress_bar method."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        bar = PipBoyDecorations.make_progress_bar(0.5)
        assert isinstance(bar, str)
        assert "[" in bar and "]" in bar
    
    def test_make_status_line_method(self):
        """Test make_status_line method."""
        from nexus.ui.skins.pipboy import PipBoyDecorations
        line = PipBoyDecorations.make_status_line("Status", "OK", "ok")
        assert isinstance(line, str)
        assert "Status" in line


class TestPipBoyHeatmapColors:
    """Test the heatmap color generator."""
    
    def test_heatmap_colors_class_exists(self):
        """Test PipBoyHeatmapColors class exists."""
        from nexus.ui.skins.pipboy import PipBoyHeatmapColors
        assert PipBoyHeatmapColors is not None
    
    def test_get_color_for_intensity_method(self):
        """Test heatmap returns color for intensity."""
        from nexus.ui.skins.pipboy import PipBoyHeatmapColors
        color = PipBoyHeatmapColors.get_color_for_intensity(0.5)
        assert isinstance(color, str)
        assert color.startswith('#')
    
    def test_heatmap_gradient_range(self):
        """Test heatmap handles full intensity range."""
        from nexus.ui.skins.pipboy import PipBoyHeatmapColors
        # Test various intensities
        for intensity in [0.0, 0.25, 0.5, 0.75, 1.0]:
            color = PipBoyHeatmapColors.get_color_for_intensity(intensity)
            assert color.startswith('#')
    
    def test_heatmap_clamps_values(self):
        """Test heatmap clamps out-of-range values."""
        from nexus.ui.skins.pipboy import PipBoyHeatmapColors
        # Should not crash on out-of-range values
        color_low = PipBoyHeatmapColors.get_color_for_intensity(-0.5)
        color_high = PipBoyHeatmapColors.get_color_for_intensity(1.5)
        assert color_low.startswith('#')
        assert color_high.startswith('#')


class TestHelperMethods:
    """Test skin helper methods for creating styled widgets."""
    
    def test_has_create_crt_frame(self):
        """Test skin has create_crt_frame method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'create_crt_frame')
        assert callable(PipBoySkin.create_crt_frame)
    
    def test_has_create_data_card(self):
        """Test skin has create_data_card method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'create_data_card')
        assert callable(PipBoySkin.create_data_card)
    
    def test_has_create_terminal_text(self):
        """Test skin has create_terminal_text method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'create_terminal_text')
        assert callable(PipBoySkin.create_terminal_text)
    
    def test_has_create_chunky_button(self):
        """Test skin has create_chunky_button method."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'create_chunky_button')
        assert callable(PipBoySkin.create_chunky_button)
    
    def test_has_radar_helpers(self):
        """Test skin has radar helper methods."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'style_radar_canvas')
        assert hasattr(PipBoySkin, 'draw_radar_grid')
        assert hasattr(PipBoySkin, 'draw_radar_sweep')


class TestScanlineOverlay:
    """Test the scanline overlay widget."""
    
    def test_scanline_overlay_exists(self):
        """Test ScanlineOverlay class exists."""
        from nexus.ui.skins.pipboy import ScanlineOverlay
        assert ScanlineOverlay is not None
    
    def test_scanline_overlay_is_canvas(self):
        """Test ScanlineOverlay inherits from Canvas."""
        from nexus.ui.skins.pipboy import ScanlineOverlay
        import tkinter as tk
        assert issubclass(ScanlineOverlay, tk.Canvas)
    
    def test_scanline_has_draw_method(self):
        """Test ScanlineOverlay has draw_scanlines method."""
        from nexus.ui.skins.pipboy import ScanlineOverlay
        assert hasattr(ScanlineOverlay, 'draw_scanlines')


class TestPipBoyTabBar:
    """Test tab bar styling class."""
    
    def test_tab_bar_class_exists(self):
        """Test PipBoyTabBar class exists."""
        from nexus.ui.skins.pipboy import PipBoyTabBar
        assert PipBoyTabBar is not None
    
    def test_tab_bar_has_restyle_method(self):
        """Test PipBoyTabBar has restyle_tabs method."""
        from nexus.ui.skins.pipboy import PipBoyTabBar
        assert hasattr(PipBoyTabBar, 'restyle_tabs')


class TestAppIntegration:
    """Test integration with main app.py."""
    
    def test_theme_added_to_app(self):
        """Test PIPBOY_THEME can be used in app context."""
        from nexus.ui.skins import PIPBOY_THEME
        # Theme should be compatible with app.py ui_themes dict
        assert 'name' in PIPBOY_THEME
        assert 'bg_main' in PIPBOY_THEME
        assert 'text_primary' in PIPBOY_THEME
    
    def test_app_imports_skin(self):
        """Test app.py can import skin module."""
        # This import chain should work
        from nexus.ui.skins import get_pipboy_skin, PIPBOY_THEME
        # These are what app.py imports
        assert callable(get_pipboy_skin)
        assert isinstance(PIPBOY_THEME, dict)
    
    def test_app_module_imports_without_error(self):
        """Test that app.py imports correctly with skin."""
        # Should not raise import errors
        from nexus import app
        assert hasattr(app, 'NexusApp')


class TestOfflineOperation:
    """Test 100% offline operation."""
    
    def test_no_network_imports(self):
        """Test skin module doesn't import network libraries."""
        from nexus.ui.skins import pipboy
        import inspect
        source = inspect.getsource(pipboy)
        # No network library imports
        assert 'import urllib' not in source
        assert 'import requests' not in source
        assert 'import http.client' not in source
    
    def test_no_external_assets(self):
        """Test skin doesn't reference external URLs or files."""
        from nexus.ui.skins import pipboy
        import inspect
        source = inspect.getsource(pipboy)
        # No URLs
        assert 'http://' not in source
        assert 'https://' not in source
    
    def test_static_data_only(self):
        """Test all skin data is static/embedded."""
        from nexus.ui.skins.pipboy import PipBoyPalette, PipBoyFonts
        # Colors are static class attributes
        assert PipBoyPalette.GREEN_PRIMARY is not None
        # Fonts are static lists
        assert PipBoyFonts.TERMINAL_FONTS is not None


class TestPassiveCompliance:
    """Test skin is non-destructive and passive."""
    
    def test_revert_method_exists(self):
        """Test revert method exists for state restoration."""
        from nexus.ui.skins.pipboy import PipBoySkin
        assert hasattr(PipBoySkin, 'revert')
        assert callable(PipBoySkin.revert)
    
    def test_skin_class_stores_original_state(self):
        """Test skin class has mechanism to store original state."""
        from nexus.ui.skins.pipboy import PipBoySkin
        import inspect
        source = inspect.getsource(PipBoySkin.__init__)
        # Should have original styles storage
        assert '_original_styles' in source
    
    def test_no_global_state_on_import(self):
        """Test skin doesn't modify global state on import."""
        from nexus.ui.skins import pipboy
        # Global skin should be None until explicitly created
        assert pipboy._pipboy_skin is None or isinstance(pipboy._pipboy_skin, pipboy.PipBoySkin)

