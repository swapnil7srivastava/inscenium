# Inscenium™ Architecture

## System Overview

Inscenium is a comprehensive placement management system that makes video scenes "addressable" by detecting, analyzing, and packaging placement opportunities for brand integration. The system operates on the principle of **Scene Graph Intelligence (SGI)** - building comprehensive understanding of video content to enable precise, contextually-aware placement.

## Core Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PERCEPTION    │───▶│       SGI       │───▶│     RENDER      │
│                 │    │                 │    │                 │
│ • Depth (MiDaS) │    │ • Scene Graph   │    │ • CUDA Comp     │
│ • Flow (RAFT)   │    │ • Surface Match │    │ • QC Metrics    │
│ • Surfels       │    │ • Rights Ledger │    │ • Sidecar Pack  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      EDGE       │    │     MEASURE     │    │    CONTROL     │
│                 │    │                 │    │                 │
│ • Real-time     │    │ • PRS Scoring   │    │ • API Gateway   │
│ • Lightweight   │    │ • Analytics     │    │ • CMS Web App   │
│ • Optimization  │    │ • Exposure Geo  │    │ • Rights Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Module Descriptions

### Perception Module
**Purpose**: Computer vision and scene understanding

**Components**:
- `depth_midas.py` - Monocular depth estimation using MiDaS models
- `flow_raft.py` - Optical flow estimation using RAFT for motion analysis  
- `surfel_proposals.py` - 3D surface element proposal generation

**Key Features**:
- Multi-modal perception pipeline
- Real-time depth and motion estimation
- Surface geometry analysis
- Temporal consistency tracking

### SGI Module (Scene Graph Intelligence)
**Purpose**: High-level scene understanding and opportunity matching

**Components**:
- `sgi_builder.py` - Build comprehensive scene graphs from perception data
- `sgi_matcher.py` - Match detected surfaces to placement opportunities
- `rights_ledger.py` - Manage placement rights and licensing compliance

**Key Features**:
- Spatial-temporal relationship modeling
- Multi-criteria opportunity scoring (PRS)
- Brand safety analysis
- Rights management integration

### Render Module
**Purpose**: Compositing and quality control

**Components**:
- `compositor_bindings.py` - CUDA-accelerated compositing engine
- `qc_metrics.py` - Placement Readiness Score (PRS) calculation
- `sidecar_packager.py` - Metadata packaging for distribution

**Key Features**:
- GPU-accelerated real-time compositing
- Comprehensive quality scoring (technical, temporal, spatial, brand safety)
- Multi-format sidecar generation (JSON, XML, CSV)

### Control Module
**Purpose**: API management and user interfaces

**Components**:
- `api/` - Go-based API gateway with authentication
- `cms/webapp/` - React/Next.js management interface
- Database integration and user management

**Key Features**:
- RESTful API with OpenAPI specification
- Modern React-based CMS interface
- Role-based access control
- Real-time dashboard and analytics

### Edge Module
**Purpose**: Optimized edge deployment

**Components**:
- `edge_processor.py` - Lightweight processing for edge scenarios

**Key Features**:
- Mobile/IoT optimized models
- Real-time processing with minimal resources
- Adaptive quality based on device capabilities

### Measure Module
**Purpose**: Analytics and performance measurement

**Components**:
- `prs_meter.py` - PRS scoring and measurement
- `exposure_geom.py` - Geometric exposure analysis
- `event_emitter.py` - Event tracking and analytics

## Data Flow

### Processing Pipeline

1. **Ingestion**: Video content enters the system
2. **Perception**: Multi-modal analysis (depth, flow, surfaces)
3. **SGI Building**: Scene graph construction with relationships
4. **Opportunity Matching**: Surface-to-placement matching with PRS scoring
5. **Rights Validation**: Licensing and compliance checking
6. **Quality Control**: Comprehensive quality assessment
7. **Packaging**: Sidecar generation for distribution
8. **Delivery**: API serving and CMS management

### Key Data Structures

```python
# Scene Graph Node
@dataclass
class SceneNode:
    node_id: str
    node_type: str  # object, surface, region
    confidence: float
    attributes: Dict[str, Any]
    frame_range: Tuple[int, int]

# Placement Opportunity  
@dataclass
class PlacementOpportunity:
    opportunity_id: str
    surface_id: str
    prs_score: float
    placement_type: str
    rights_status: str
    quality_metrics: Dict[str, Any]

# PRS Components
@dataclass  
class PRSComponents:
    technical_score: float
    visibility_score: float
    temporal_score: float
    spatial_score: float
    brand_safety_score: float
    final_prs: float
```

## Technology Stack

### Languages
- **Python**: Core perception and ML pipeline
- **Go**: API gateway and high-performance services  
- **Rust**: Performance-critical components
- **TypeScript/React**: Frontend CMS interface
- **CUDA/C++**: GPU acceleration

### Key Dependencies
- **Computer Vision**: OpenCV, MiDaS, RAFT
- **Deep Learning**: PyTorch, ONNX
- **Database**: PostgreSQL, Redis
- **Web Framework**: Next.js, Gin (Go)
- **Containerization**: Docker, Kubernetes
- **CI/CD**: GitHub Actions, pre-commit

## Deployment Architecture

### Production Deployment
```
                    ┌─ Load Balancer ─┐
                    │                 │
        ┌─── API Gateway (Go) ────┐   │
        │                        │   │
        ▼                        ▼   │
┌─ CMS Web App ─┐     ┌─ Processing Pipeline ─┐
│   (Next.js)   │     │     (Python)          │
│   • Dashboard │     │   • Perception        │
│   • Analytics │     │   • SGI               │
│   • Rights    │     │   • Render            │
└───────────────┘     └───────────────────────┘
        │                        │
        ▼                        ▼
┌─ PostgreSQL ─┐       ┌─ Redis Cache ─┐
│   • Metadata │       │   • Sessions  │
│   • Rights   │       │   • Analytics │
│   • Users    │       │   • Cache     │
└──────────────┘       └───────────────┘
```

### Edge Deployment
- Lightweight models optimized for mobile/IoT
- Adaptive processing based on device capabilities
- Local processing with cloud sync

## Security & Compliance

### Data Protection
- Encryption at rest and in transit
- Role-based access control (RBAC)
- Audit logging for all operations
- GDPR compliance for user data

### Rights Management
- Digital rights ledger with blockchain integration
- Territory and media rights enforcement
- Brand safety validation
- Content compliance scoring

## Performance Characteristics

### Processing Speed
- **Real-time**: 30+ FPS on GPU hardware
- **Edge**: 15+ FPS on mobile devices
- **Batch**: 100x real-time on server hardware

### Quality Metrics
- **PRS Accuracy**: >90% correlation with human evaluation
- **Brand Safety**: >95% accuracy in content classification
- **Temporal Stability**: <5% variance across similar scenes

### Scalability
- Horizontal scaling via containerization
- Asynchronous processing pipeline
- Distributed compute across multiple GPUs
- Cloud-native architecture

## Future Roadmap

### Planned Enhancements
1. **ML Pipeline**: Automated model retraining
2. **Real-time Streaming**: Live processing capability
3. **AR/VR Integration**: Extended reality placement
4. **Blockchain Rights**: Distributed rights ledger
5. **Advanced Analytics**: Predictive opportunity scoring

### Research Areas
- Neural scene representations
- Temporal-aware placement optimization
- Cross-modal scene understanding
- Automated brand safety classification