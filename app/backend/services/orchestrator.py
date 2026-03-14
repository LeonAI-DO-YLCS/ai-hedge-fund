from sqlalchemy.orm import Session
from app.backend.database.connection import SessionLocal
from app.backend.repositories.flow_repository import FlowRepository
from app.backend.repositories.flow_manifest_repository import FlowManifestRepository
from app.backend.services.flow_manifest_service import FlowManifestService
from app.backend.services.flow_compiler_service import FlowCompilerService
from app.backend.services.flow_catalog_service import FlowCatalogService
from app.backend.services.mt5_symbol_resolver_service import MT5SymbolResolverService
from app.backend.services.run_orchestrator_service import RunOrchestratorService

def get_orchestrator_instance() -> RunOrchestratorService:
    """Factory to create a RunOrchestratorService with its dependencies."""
    db: Session = SessionLocal()
    try:
        m_repo = FlowManifestRepository(db)
        m_service = FlowManifestService(m_repo)
        
        catalog = FlowCatalogService()
        resolver = MT5SymbolResolverService()
        compiler = FlowCompilerService(catalog, resolver)
        
        run_repo = FlowRepository(db)
        return RunOrchestratorService(m_service, compiler, run_repo)
    finally:
        db.close()

# Singleton instance for across-service event sharing
run_orchestrator = get_orchestrator_instance()
