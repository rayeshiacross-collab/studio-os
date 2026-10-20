import asyncio
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from .state_machine import StateMachine, ProductionState, InvalidTransitionError
from .approval import ApprovalGate, ApprovalRejectedError
from .dependency_graph import DependencyGraph, AssetNode, CircularDependencyError
from .cost_tracker import CostTracker, BudgetExceededError
from .checkpoint import CheckpointManager
from .safety import ContentSafety, SafetyViolationError
from .resources import ResourcePool
from .quality import QualityEvaluator
from .character_consistency import CharacterConsistencyEngine
from .models import Project, Screenplay, Platform, RenderJob

class LoopType(Enum):
    ARTIST = "artist"      # High quality features
    PLATFORM = "platform"  # SaaS for authors
    FARM = "farm"          # High volume shorts
    SERIES = "series"      # Multi-episode with strict character lock

@dataclass
class ProductionOrder:
    id: str
    loop: LoopType
    project_id: str
    platform: Platform
    priority: int = 0
    budget_limit: float = 1000.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

class Orchestrator:
    """Central nervous system of Studio OS."""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.approval_gate = ApprovalGate(kernel)
        self.cost_tracker = CostTracker()
        self.safety = ContentSafety()
        self.resource_pool = ResourcePool()
        self.quality = QualityEvaluator()
        self.character_engine = CharacterConsistencyEngine()
        
        self.active_productions: Dict[str, ProductionOrder] = {}
        self.completed_productions: List[str] = []
        self.failed_productions: Dict[str, str] = {}
        
        self.loop_configs = {
            LoopType.ARTIST: {
                "max_concurrent": 1,
                "require_approval": True,
                "quality_threshold": 0.95,
                "max_cost_per_minute": 500.0,
                "retry_limit": 3
            },
            LoopType.PLATFORM: {
                "max_concurrent": 5,
                "require_approval": False,
                "quality_threshold": 0.80,
                "max_cost_per_minute": 100.0,
                "retry_limit": 2
            },
            LoopType.FARM: {
                "max_concurrent": 20,
                "require_approval": False,
                "quality_threshold": 0.60,
                "max_cost_per_minute": 10.0,
                "retry_limit": 1
            },
            LoopType.SERIES: {
                "max_concurrent": 2,
                "require_approval": True,
                "quality_threshold": 0.90,
                "max_cost_per_minute": 150.0,
                "retry_limit": 3,
                "strict_character_lock": True
            }
        }
        
        self._shutdown = False
    
    # ... remaining methods from original submission 04 preserved ...
    # Full implementation includes queue processing, stage methods,
    # health monitoring, and character conditioning injection points.
