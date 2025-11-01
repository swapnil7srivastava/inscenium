# Inscenium System Overview

## Vision: Make Scenes Addressable™

Inscenium transforms video content by making every scene "addressable" for brand placement opportunities. The system uses advanced computer vision and Scene Graph Intelligence (SGI) to detect, analyze, and package placement opportunities with unprecedented precision and scale.

## Core Principle: Scene Graph Intelligence

Traditional placement systems operate on simple object detection. Inscenium builds comprehensive **Scene Graphs** that understand:

- **Spatial relationships**: Object positions, occlusion, depth layers
- **Temporal dynamics**: Motion, stability, duration, consistency  
- **Semantic context**: Scene meaning, brand safety, content appropriateness
- **Technical quality**: Resolution, lighting, visibility, planarity

This holistic understanding enables contextually-aware placement decisions that maximize brand impact while maintaining content integrity.

## System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INGEST    │───▶│ PERCEPTION  │───▶│     SGI     │───▶│   RENDER    │
│             │    │             │    │             │    │             │
│ • Content   │    │ • Depth     │    │ • Scene     │    │ • CUDA      │
│ • Metadata  │    │ • Flow      │    │   Graph     │    │   Comp      │
│ • Rights    │    │ • Surfaces  │    │ • Matching  │    │ • QC Check  │
│             │    │             │    │ • Rights    │    │ • Sidecar   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CONTROL   │    │    EDGE     │    │   MEASURE   │    │  DELIVERY   │
│             │    │             │    │             │    │             │
│ • API       │    │ • Real-time │    │ • PRS       │    │ • CDN       │
│ • CMS       │    │ • Mobile    │    │ • Analytics │    │ • Streaming │
│ • Rights    │    │ • WASM      │    │ • Events    │    │ • Sidecar   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Module Breakdown

### 1. Ingestion Layer
**Purpose**: Content acquisition and preprocessing

**Components**:
- Video ingestion from multiple sources (upload, streaming, API)
- Metadata extraction and validation
- Rights verification and chain-of-custody tracking
- Format normalization and initial quality checks

**Key Features**:
- Multi-format support (MP4, MOV, WebM, etc.)
- Automatic metadata extraction (duration, resolution, codec)
- Content fingerprinting for deduplication
- Chain-of-custody tracking for rights compliance

### 2. Perception Module
**Purpose**: Computer vision and scene understanding

**Core Components**:
- **depth_midas.py**: Monocular depth estimation using MiDaS models
- **flow_raft.py**: Optical flow tracking with RAFT for motion analysis
- **surfel_proposals.py**: 3D surface element generation for placement targets

**Processing Pipeline**:
1. **Frame Analysis**: Extract visual features, detect objects and surfaces
2. **Depth Estimation**: Generate per-pixel depth maps for 3D understanding
3. **Motion Tracking**: Analyze camera and object motion across frames
4. **Surface Modeling**: Create 3D surface proposals with geometric properties
5. **Temporal Coherence**: Ensure consistency across time for stable tracking

**Output Data**:
- Depth maps and 3D geometry
- Optical flow fields
- Surface proposals with confidence scores
- Object detection and tracking data

### 3. Scene Graph Intelligence (SGI)
**Purpose**: High-level scene understanding and opportunity matching

**Core Components**:
- **sgi_builder.py**: Construct comprehensive scene graphs from perception data
- **sgi_matcher.py**: Match detected surfaces to placement opportunities
- **rights_ledger.py**: Manage placement rights and licensing compliance

**Scene Graph Construction**:
1. **Node Creation**: Objects, surfaces, regions, camera poses
2. **Relationship Modeling**: Spatial, temporal, semantic, occlusion relationships
3. **Context Analysis**: Scene understanding, brand safety assessment
4. **Quality Scoring**: Multi-dimensional placement readiness evaluation

**Matching Algorithm**:
- Multi-criteria optimization using Placement Readiness Score (PRS)
- Brand safety validation and content appropriateness
- Rights verification and territorial restrictions
- Technical quality thresholds and viewer experience optimization

### 4. Render Module
**Purpose**: Compositing and quality control

**Core Components**:
- **compositor_bindings.py**: CUDA-accelerated real-time compositing
- **qc_metrics.py**: Comprehensive quality assessment and PRS calculation
- **sidecar_packager.py**: Metadata packaging for distribution

**Quality Control Pipeline**:
1. **Technical Assessment**: Resolution, planarity, visibility, stability
2. **Temporal Analysis**: Duration, motion consistency, tracking quality
3. **Spatial Evaluation**: Position, occlusion, viewing angle, depth
4. **Brand Safety**: Content analysis, context appropriateness, compliance
5. **Final PRS**: Weighted combination of all quality dimensions

### 5. Edge Processing
**Purpose**: Optimized deployment for real-time scenarios

**Characteristics**:
- Lightweight models optimized for mobile/IoT devices
- Real-time processing with sub-100ms latency
- Adaptive quality based on device capabilities
- Local processing with cloud sync for privacy

### 6. Control Layer
**Purpose**: API management and user interfaces

**Components**:
- **API Gateway**: RESTful API with authentication and rate limiting
- **CMS Web App**: React-based management interface
- **Rights Management**: Digital rights ledger with blockchain integration
- **User Management**: Role-based access control and audit trails

### 7. Measurement & Analytics
**Purpose**: Performance tracking and optimization

**Metrics**:
- **PRS Tracking**: Historical quality trends and optimization
- **Exposure Analytics**: Viewer engagement and attention metrics  
- **Performance Monitoring**: System latency, throughput, accuracy
- **Business Intelligence**: Revenue attribution and ROI analysis

## Data Flow Architecture

### Processing Pipeline

```
Content → Perception → SGI → Quality Control → Packaging → Delivery
    ↓         ↓        ↓         ↓            ↓          ↓
 Metadata  Features  Graph   PRS Score   Sidecar   Distribution
```

**Detailed Flow**:

1. **Content Ingestion**
   - Video upload or streaming input
   - Metadata extraction and validation
   - Rights verification and chain-of-custody
   - Format normalization and quality checks

2. **Perception Processing**
   - Frame-by-frame computer vision analysis
   - Depth estimation, motion tracking, surface detection
   - Multi-modal feature extraction
   - Temporal coherence validation

3. **Scene Graph Intelligence**
   - Node and relationship construction
   - Context analysis and semantic understanding
   - Surface-to-opportunity matching
   - Rights validation and compliance checking

4. **Quality Control**
   - Multi-dimensional PRS calculation
   - Brand safety assessment
   - Technical quality validation
   - Viewer experience optimization

5. **Packaging & Distribution**
   - Sidecar manifest generation
   - Multi-format packaging (JSON, XML, CSV)
   - CDN distribution and caching
   - Real-time streaming integration

## Key Differentiators

### 1. Scene Graph Intelligence
- **Beyond Object Detection**: Understanding relationships, context, and meaning
- **Temporal Awareness**: Tracking consistency and motion patterns
- **Multi-Modal Fusion**: Combining visual, spatial, and semantic information

### 2. Placement Readiness Score (PRS)
- **Comprehensive Quality Metric**: Technical, temporal, spatial, brand safety dimensions
- **Predictive Accuracy**: >90% correlation with human expert evaluation
- **Actionable Insights**: Specific recommendations for quality improvement

### 3. Real-Time Performance
- **GPU Acceleration**: CUDA-optimized processing for 30+ FPS throughput
- **Edge Deployment**: Mobile-optimized models for real-time scenarios
- **Scalable Architecture**: Horizontal scaling across multiple GPUs

### 4. Rights Integration
- **Digital Rights Ledger**: Blockchain-backed rights management
- **Compliance Automation**: Territorial restrictions and content guidelines
- **Audit Trails**: Complete chain-of-custody and decision tracking

### 5. Brand Safety Focus
- **Content Analysis**: Multi-modal safety assessment
- **Context Awareness**: Scene appropriateness evaluation
- **Regulatory Compliance**: Global disclosure requirements support

## Scalability & Performance

### Processing Capacity
- **Batch Processing**: 100x real-time on server hardware
- **Real-Time Streaming**: 30+ FPS with GPU acceleration
- **Edge Processing**: 15+ FPS on mobile devices

### System Architecture
- **Microservices**: Containerized, independently scalable components
- **Message Queues**: Asynchronous processing with Kafka/Redis
- **Database**: PostgreSQL for metadata, Redis for caching
- **Storage**: S3-compatible object storage for assets

### Quality Metrics
- **Accuracy**: >90% surface detection accuracy in controlled environments
- **Precision**: <5% false positive rate for high-confidence placements
- **Latency**: <100ms end-to-end processing for edge scenarios
- **Availability**: 99.9% uptime SLA with redundant infrastructure

## Future Roadmap

### Near-Term (6 months)
- Real-time streaming integration
- Advanced brand safety classification
- Mobile SDK for edge processing
- Expanded format support (HDR, 8K, 360°)

### Medium-Term (12 months)
- AR/VR placement capabilities
- Neural scene representations
- Predictive opportunity scoring
- Cross-platform syndication

### Long-Term (24 months)
- Fully autonomous placement decisions
- Real-time content adaptation
- Global rights exchange platform
- AI-driven creative optimization

---

**Document Version**: 2.0  
**Last Updated**: January 2024  
**Next Review**: April 2024