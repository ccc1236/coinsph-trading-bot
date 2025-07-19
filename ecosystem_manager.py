import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class AssetInsight:
    """Asset research insight data structure"""
    symbol: str
    volatility: float
    performance_score: float
    recommended_strategy: str
    last_analyzed: str
    risk_level: str
    trade_frequency: str
    
@dataclass
class OptimizationResult:
    """Optimization result data structure"""
    symbol: str
    tool: str  # 'prophet', 'backtest', etc.
    buy_threshold: float
    sell_threshold: float
    take_profit: float
    expected_return: float
    win_rate: float
    total_trades: int
    optimization_date: str
    
@dataclass
class UserPreferences:
    """User preferences data structure"""
    default_base_amount: float = 200
    preferred_position_sizing: str = "adaptive"
    risk_tolerance: str = "medium"
    max_trades_per_day: int = 10
    preferred_assets: List[str] = None
    
    def __post_init__(self):
        if self.preferred_assets is None:
            self.preferred_assets = []

class EcosystemManager:
    """
    🌐 Ecosystem Manager v1 - Central Data Management
    
    Manages cross-tool communication, shared configuration, and ecosystem insights
    for the trading bot ecosystem (PROPHET, TITAN, momentum_backtest, etc.)
    
    Features:
    - ✅ Shared configuration management
    - ✅ Cross-tool data sharing
    - ✅ Asset insights and recommendations
    - ✅ Optimization result tracking
    - ✅ User preference management
    - ✅ Ecosystem health monitoring
    """
    
    def __init__(self, config_dir: str = "ecosystem_data"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # File paths
        self.ecosystem_config_file = self.config_dir / "ecosystem_config.json"
        self.research_insights_file = self.config_dir / "research_insights.json"
        self.optimization_history_file = self.config_dir / "optimization_history.json"
        self.user_preferences_file = self.config_dir / "user_preferences.json"
        
        # Setup logging
        self.logger = logging.getLogger('EcosystemManager')
        
        # Initialize data structures
        self.user_preferences = self.load_user_preferences()
        self.ecosystem_config = self.load_ecosystem_config()
        
        self.logger.info("🌐 Ecosystem Manager v1 initialized")
        self.logger.info(f"📁 Data directory: {self.config_dir.absolute()}")

    def load_ecosystem_config(self) -> Dict[str, Any]:
        """Load main ecosystem configuration"""
        try:
            if self.ecosystem_config_file.exists():
                with open(self.ecosystem_config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info("✅ Loaded existing ecosystem configuration")
                return config
            else:
                # Create default configuration
                default_config = {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "tools": {
                        "prophet": {"version": "3.1", "last_used": None},
                        "titan": {"version": "4.2", "last_used": None},
                        "momentum_backtest": {"version": "4.7", "last_used": None},
                        "oracle": {"version": "5.0", "last_used": None}
                    },
                    "ecosystem_health": {
                        "active_optimizations": 0,
                        "total_insights": 0,
                        "last_research_date": None
                    }
                }
                self.save_ecosystem_config(default_config)
                self.logger.info("🆕 Created new ecosystem configuration")
                return default_config
                
        except Exception as e:
            self.logger.error(f"❌ Error loading ecosystem config: {e}")
            return {}

    def save_ecosystem_config(self, config: Dict[str, Any]) -> bool:
        """Save ecosystem configuration"""
        try:
            config['last_updated'] = datetime.now().isoformat()
            with open(self.ecosystem_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.ecosystem_config = config
            return True
        except Exception as e:
            self.logger.error(f"❌ Error saving ecosystem config: {e}")
            return False

    def load_user_preferences(self) -> UserPreferences:
        """Load user preferences"""
        try:
            if self.user_preferences_file.exists():
                with open(self.user_preferences_file, 'r') as f:
                    data = json.load(f)
                prefs = UserPreferences(**data)
                self.logger.info("✅ Loaded user preferences")
                return prefs
            else:
                prefs = UserPreferences()
                self.save_user_preferences(prefs)
                self.logger.info("🆕 Created default user preferences")
                return prefs
                
        except Exception as e:
            self.logger.error(f"❌ Error loading user preferences: {e}")
            return UserPreferences()

    def save_user_preferences(self, preferences: UserPreferences) -> bool:
        """Save user preferences"""
        try:
            with open(self.user_preferences_file, 'w') as f:
                json.dump(asdict(preferences), f, indent=2)
            self.user_preferences = preferences
            self.logger.info("💾 Saved user preferences")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error saving user preferences: {e}")
            return False

    def update_tool_usage(self, tool_name: str, version: str = None):
        """Update tool usage tracking"""
        try:
            if version:
                self.ecosystem_config['tools'][tool_name]['version'] = version
            self.ecosystem_config['tools'][tool_name]['last_used'] = datetime.now().isoformat()
            self.save_ecosystem_config(self.ecosystem_config)
            self.logger.info(f"📊 Updated {tool_name} usage tracking")
        except Exception as e:
            self.logger.error(f"❌ Error updating tool usage: {e}")

    def save_research_insights(self, insights: List[AssetInsight]) -> bool:
        """Save research insights from momentum_backtest"""
        try:
            insights_data = {
                'generated_date': datetime.now().isoformat(),
                'total_assets': len(insights),
                'insights': [asdict(insight) for insight in insights]
            }
            
            with open(self.research_insights_file, 'w') as f:
                json.dump(insights_data, f, indent=2)
            
            # Update ecosystem health
            self.ecosystem_config['ecosystem_health']['total_insights'] = len(insights)
            self.ecosystem_config['ecosystem_health']['last_research_date'] = datetime.now().isoformat()
            self.save_ecosystem_config(self.ecosystem_config)
            
            self.logger.info(f"💾 Saved {len(insights)} research insights")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving research insights: {e}")
            return False

    def load_research_insights(self) -> List[AssetInsight]:
        """Load research insights"""
        try:
            if self.research_insights_file.exists():
                with open(self.research_insights_file, 'r') as f:
                    data = json.load(f)
                
                insights = [AssetInsight(**insight) for insight in data['insights']]
                self.logger.info(f"✅ Loaded {len(insights)} research insights")
                return insights
            else:
                self.logger.info("📭 No research insights found")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error loading research insights: {e}")
            return []

    def get_top_assets(self, limit: int = 5, risk_level: str = None) -> List[AssetInsight]:
        """Get top recommended assets based on research insights"""
        insights = self.load_research_insights()
        
        if not insights:
            return []
        
        # Filter by risk level if specified
        if risk_level:
            insights = [i for i in insights if i.risk_level == risk_level]
        
        # Sort by performance score
        insights.sort(key=lambda x: x.performance_score, reverse=True)
        
        return insights[:limit]

    def load_optimization_history(self) -> List[Dict[str, Any]]:
        """Load optimization history with improved error handling"""
        try:
            if self.optimization_history_file.exists():
                with open(self.optimization_history_file, 'r') as f:
                    data = json.load(f)
                return data.get('results', [])
            else:
                return []
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decode error in optimization history: {e}")
            self.logger.info("🔧 Attempting to recover by backing up corrupted file and creating new one")
            
            # Backup the corrupted file
            try:
                backup_name = f"{self.optimization_history_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.optimization_history_file.rename(backup_name)
                self.logger.info(f"📁 Corrupted file backed up as: {backup_name}")
            except Exception as backup_error:
                self.logger.error(f"❌ Could not backup corrupted file: {backup_error}")
            
            # Create fresh optimization history file
            try:
                fresh_data = {
                    'last_updated': datetime.now().isoformat(),
                    'total_optimizations': 0,
                    'results': []
                }
                with open(self.optimization_history_file, 'w') as f:
                    json.dump(fresh_data, f, indent=2)
                self.logger.info("✅ Created fresh optimization history file")
                return []
            except Exception as create_error:
                self.logger.error(f"❌ Could not create fresh file: {create_error}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error loading optimization history: {e}")
            return []

    def save_optimization_result(self, result: OptimizationResult) -> bool:
        """Save optimization result with improved error handling"""
        try:
            # Load existing results with error recovery
            optimization_history = self.load_optimization_history()
            
            # Add new result
            optimization_history.append(asdict(result))
            
            # Save updated history with atomic write
            temp_file = f"{self.optimization_history_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'total_optimizations': len(optimization_history),
                    'results': optimization_history
                }, f, indent=2)
            
            # Atomic rename to replace the original file
            import os
            os.replace(temp_file, self.optimization_history_file)
            
            # Update ecosystem health
            self.ecosystem_config['ecosystem_health']['active_optimizations'] = len(optimization_history)
            self.save_ecosystem_config(self.ecosystem_config)
            
            self.logger.info(f"💾 Saved optimization result for {result.symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving optimization result: {e}")
            # Clean up temp file if it exists
            temp_file = f"{self.optimization_history_file}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False

    def get_latest_optimization(self, symbol: str) -> Optional[OptimizationResult]:
        """Get latest optimization result for a symbol"""
        history = self.load_optimization_history()
        
        # Find latest optimization for this symbol
        symbol_results = [r for r in history if r['symbol'] == symbol]
        if not symbol_results:
            return None
        
        # Sort by date and return latest
        symbol_results.sort(key=lambda x: x['optimization_date'], reverse=True)
        latest = symbol_results[0]
        
        return OptimizationResult(**latest)

    def get_smart_recommendations(self, tool_name: str) -> Dict[str, Any]:
        """Get smart recommendations for a specific tool"""
        recommendations = {
            'suggested_assets': [],
            'recommended_parameters': {},
            'workflow_suggestions': [],
            'performance_insights': {}
        }
        
        try:
            # Get top assets from research
            top_assets = self.get_top_assets(limit=3)
            recommendations['suggested_assets'] = [
                {
                    'symbol': asset.symbol,
                    'reason': f"{asset.risk_level.title()} risk, {asset.performance_score:.1f}% performance",
                    'strategy': asset.recommended_strategy
                }
                for asset in top_assets
            ]
            
            # Tool-specific recommendations
            if tool_name == 'prophet':
                recommendations['workflow_suggestions'] = [
                    "Consider testing top-performing assets from research insights",
                    "Use volatility-based parameter ranges for optimization",
                    "Review recent optimization history for similar assets"
                ]
                
                # Get recent successful optimizations
                recent_optimizations = self.load_optimization_history()
                if recent_optimizations:
                    recent = recent_optimizations[-3:]  # Last 3
                    recommendations['performance_insights'] = {
                        'recent_avg_return': sum(r.get('expected_return', 0) for r in recent) / len(recent),
                        'recent_avg_winrate': sum(r.get('win_rate', 0) for r in recent) / len(recent),
                        'trending_parameters': self._analyze_parameter_trends(recent)
                    }
            
            elif tool_name == 'titan':
                recommendations['workflow_suggestions'] = [
                    "Load Prophet's latest optimization results",
                    "Consider assets with proven research performance",
                    "Use adaptive position sizing for optimal results"
                ]
                
                # Check for available Prophet recommendations
                if (Path('prophet_reco.json')).exists():
                    recommendations['recommended_parameters'] = {
                        'source': 'prophet_recommendations',
                        'available': True,
                        'suggestion': 'Load Prophet recommendations for optimal parameters'
                    }
            
            self.logger.info(f"🧠 Generated smart recommendations for {tool_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error generating recommendations: {e}")
        
        return recommendations

    def _analyze_parameter_trends(self, recent_results: List[Dict]) -> Dict[str, float]:
        """Analyze trending parameters from recent optimizations"""
        if not recent_results:
            return {}
        
        try:
            avg_buy = sum(r.get('buy_threshold', 0) for r in recent_results) / len(recent_results)
            avg_sell = sum(r.get('sell_threshold', 0) for r in recent_results) / len(recent_results)
            avg_tp = sum(r.get('take_profit', 0) for r in recent_results) / len(recent_results)
            
            return {
                'trending_buy_threshold': avg_buy,
                'trending_sell_threshold': avg_sell,
                'trending_take_profit': avg_tp
            }
        except:
            return {}

    def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status"""
        status = {
            'ecosystem_version': '1.0',
            'last_updated': self.ecosystem_config.get('last_updated'),
            'health': self.ecosystem_config.get('ecosystem_health', {}),
            'tools': self.ecosystem_config.get('tools', {}),
            'data_summary': {},
            'recommendations_available': False
        }
        
        try:
            # Check data availability
            status['data_summary'] = {
                'research_insights': len(self.load_research_insights()),
                'optimization_history': len(self.load_optimization_history()),
                'user_preferences_set': self.user_preferences_file.exists(),
                'prophet_recommendations': Path('prophet_reco.json').exists()
            }
            
            # Check if recommendations are available
            status['recommendations_available'] = (
                status['data_summary']['research_insights'] > 0 or
                status['data_summary']['optimization_history'] > 0
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error getting ecosystem status: {e}")
        
        return status

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old ecosystem data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean optimization history
            history = self.load_optimization_history()
            cleaned_history = [
                r for r in history 
                if datetime.fromisoformat(r.get('optimization_date', '1970-01-01')) > cutoff_date
            ]
            
            if len(cleaned_history) < len(history):
                with open(self.optimization_history_file, 'w') as f:
                    json.dump({
                        'last_updated': datetime.now().isoformat(),
                        'total_optimizations': len(cleaned_history),
                        'results': cleaned_history
                    }, f, indent=2)
                
                removed_count = len(history) - len(cleaned_history)
                self.logger.info(f"🧹 Cleaned up {removed_count} old optimization records")
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")

# Utility functions for other tools to use

def get_ecosystem_manager() -> EcosystemManager:
    """Get a shared ecosystem manager instance"""
    return EcosystemManager()

def log_tool_usage(tool_name: str, version: str = None):
    """Quick function to log tool usage"""
    try:
        manager = get_ecosystem_manager()
        manager.update_tool_usage(tool_name, version)
    except:
        pass  # Fail silently if ecosystem not available

def get_asset_recommendations(tool_name: str, limit: int = 3) -> List[str]:
    """Quick function to get asset recommendations"""
    try:
        manager = get_ecosystem_manager()
        recommendations = manager.get_smart_recommendations(tool_name)
        return [asset['symbol'] for asset in recommendations['suggested_assets'][:limit]]
    except:
        return []  # Return empty list if ecosystem not available

def save_quick_insight(symbol: str, performance_score: float, risk_level: str = "medium"):
    """Quick function to save a research insight"""
    try:
        manager = get_ecosystem_manager()
        insight = AssetInsight(
            symbol=symbol,
            volatility=0.0,  # Will be updated by proper research tools
            performance_score=performance_score,
            recommended_strategy="adaptive",
            last_analyzed=datetime.now().isoformat(),
            risk_level=risk_level,
            trade_frequency="medium"
        )
        manager.save_research_insights([insight])
    except:
        pass  # Fail silently if ecosystem not available

if __name__ == "__main__":
    # Demo usage
    print("🌐 Ecosystem Manager v1 Demo")
    print("=" * 50)
    
    # Initialize ecosystem
    manager = EcosystemManager()
    
    # Show status
    status = manager.get_ecosystem_status()
    print(f"📊 Ecosystem Status:")
    print(f"   Health: {status['health']}")
    print(f"   Data Summary: {status['data_summary']}")
    print(f"   Recommendations Available: {status['recommendations_available']}")
    
    # Demo asset insight
    demo_insight = AssetInsight(
        symbol="XRPPHP",
        volatility=5.2,
        performance_score=8.7,
        recommended_strategy="adaptive",
        last_analyzed=datetime.now().isoformat(),
        risk_level="medium",
        trade_frequency="high"
    )
    
    manager.save_research_insights([demo_insight])
    print(f"\n💾 Saved demo research insight for XRPPHP")
    
    # Demo recommendations
    recommendations = manager.get_smart_recommendations('prophet')
    print(f"\n🧠 Smart recommendations for Prophet:")
    for suggestion in recommendations['workflow_suggestions']:
        print(f"   • {suggestion}")
    
    print(f"\n✅ Ecosystem Manager v1 ready for integration!")