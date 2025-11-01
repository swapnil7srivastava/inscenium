# Data Flow Architecture

## Overview

This document describes the end-to-end data flow through the Inscenium placement management system, from content ingestion to final delivery. The architecture follows a pipeline pattern with clear separation of concerns and well-defined interfaces between stages.

## High-Level Data Flow

```
[INGEST] → [PERCEPTION] → [SGI] → [RENDER/EDGE] → [MEASURE] → [EVENTS] → [DELIVERY]
```

Each stage processes data, adds value, and passes enriched information to the next stage while maintaining full traceability and audit capabilities.

## Detailed Pipeline Stages

### Stage 1: INGEST
**Input**: Raw video content, metadata, rights information  
**Output**: Normalized content with validated metadata and rights chain

#### Sequence:
1. **Content Reception**
   ```
   Video File/Stream → Content Validation → Format Detection → Initial Quality Check
   ```

2. **Metadata Extraction**
   ```
   Raw Metadata → Schema Validation → Enrichment → Normalization → Storage
   ```

3. **Rights Verification**
   ```
   Rights Claims → Chain Validation → Territory Check → License Verification → Ledger Update
   ```

4. **Data Storage**
   ```
   Content → Object Storage (S3)
   Metadata → PostgreSQL (normalized)
   Rights → Rights Ledger (blockchain-backed)
   ```

#### Key Data Structures:
```json
{
  "content_id": "uuid",
  "original_filename": "movie_trailer_v2.mp4",
  "format": {"codec": "h264", "resolution": "1920x1080", "fps": 30},
  "duration_seconds": 120.5,
  "rights": {
    "owner": "Studio Productions LLC",
    "territories": ["US", "CA", "UK"],
    "media_types": ["streaming", "broadcast"],
    "expiry": "2025-12-31"
  },
  "quality": {"bitrate": 8500, "audio_channels": 2}
}
```

### Stage 2: PERCEPTION
**Input**: Normalized video content  
**Output**: Computer vision features, depth maps, surface proposals

#### Sequence:
1. **Frame Extraction**
   ```
   Video Stream → Frame Sampling → Frame Queue → Batch Processing
   ```

2. **Multi-Modal Analysis**
   ```
   Frames → [Depth Estimation | Object Detection | Surface Analysis] → Feature Fusion
   ```

3. **Temporal Processing**
   ```
   Frame Sequence → Motion Tracking → Temporal Coherence → Stability Analysis
   ```

4. **3D Reconstruction**
   ```
   Depth + Motion → Surface Proposals → 3D Geometry → Placement Candidates
   ```

#### Processing Pipeline:
```python
# Parallel processing streams
depth_stream = MiDaSDepthEstimator().process_frames(frames)
flow_stream = RAFTFlowEstimator().process_frame_pairs(frame_pairs)
surface_stream = SurfelProposalGenerator().generate_proposals(depth_stream, flow_stream)

# Feature fusion
perception_output = PerceptionFusion().combine_streams(
    depth=depth_stream,
    flow=flow_stream, 
    surfaces=surface_stream
)
```

#### Key Data Structures:
```json
{
  "frame_id": 1250,
  "timestamp": 41.67,
  "depth_map": {"shape": [1080, 1920], "dtype": "float32", "range": [0.5, 15.0]},
  "optical_flow": {"magnitude_avg": 3.2, "direction_consistency": 0.85},
  "surfaces": [
    {
      "surface_id": "surf_001",
      "confidence": 0.92,
      "area_m2": 2.4,
      "planarity": 0.88,
      "coordinates_3d": [[x, y, z], ...],
      "surface_type": "wall"
    }
  ],
  "objects": [
    {"class": "person", "bbox": [100, 200, 150, 400], "confidence": 0.95}
  ]
}
```

### Stage 3: SGI (Scene Graph Intelligence)
**Input**: Perception features and 3D data  
**Output**: Scene graph with relationships and placement opportunities

#### Sequence:
1. **Scene Graph Construction**
   ```
   Perception Data → Node Creation → Relationship Analysis → Graph Assembly
   ```

2. **Context Analysis**
   ```
   Scene Graph → Semantic Analysis → Brand Safety Check → Context Scoring
   ```

3. **Opportunity Matching**
   ```
   Surface Nodes → Placement Criteria → Quality Assessment → PRS Calculation
   ```

4. **Rights Validation**
   ```
   Opportunities → Rights Query → Territory Check → Compliance Validation
   ```

#### Graph Construction Algorithm:
```python
def build_scene_graph(perception_data):
    # 1. Create nodes from perception data
    nodes = create_nodes_from_perception(perception_data)
    
    # 2. Analyze spatial relationships
    spatial_edges = analyze_spatial_relationships(nodes)
    
    # 3. Analyze temporal relationships  
    temporal_edges = analyze_temporal_relationships(nodes)
    
    # 4. Analyze semantic relationships
    semantic_edges = analyze_semantic_relationships(nodes)
    
    # 5. Assemble complete graph
    scene_graph = SceneGraph(
        nodes=nodes,
        edges=spatial_edges + temporal_edges + semantic_edges
    )
    
    return scene_graph
```

#### Key Data Structures:
```json
{
  "scene_graph_id": "sg_12345",
  "temporal_extent": [0, 3600],
  "nodes": [
    {
      "node_id": "surface_001",
      "node_type": "surface",
      "confidence": 0.92,
      "attributes": {
        "surface_type": "wall",
        "area_m2": 2.4,
        "planarity": 0.88,
        "placement_suitable": true
      },
      "frame_range": [100, 250]
    }
  ],
  "edges": [
    {
      "edge_id": "spatial_001", 
      "source": "surface_001",
      "target": "object_001",
      "relationship": "adjacent",
      "confidence": 0.85
    }
  ],
  "opportunities": [
    {
      "opportunity_id": "opp_001",
      "surface_id": "surface_001",
      "prs_score": 87.5,
      "placement_type": "billboard",
      "brand_safety_score": 92.0
    }
  ]
}
```

### Stage 4: RENDER/EDGE
**Input**: Scene graph with placement opportunities  
**Output**: Quality-controlled placements with compositing metadata

#### Sequence:
1. **Quality Control Assessment**
   ```
   Opportunities → PRS Calculation → Quality Thresholds → Pass/Fail Decision
   ```

2. **Compositing Preparation** 
   ```
   Validated Opportunities → Transform Calculation → Layer Setup → Render Pipeline
   ```

3. **Edge Optimization** (parallel path)
   ```
   Scene Graph → Model Compression → Mobile Optimization → Edge Deployment
   ```

4. **Sidecar Generation**
   ```
   Final Opportunities → Metadata Packaging → Multi-Format Export → Distribution Prep
   ```

#### PRS Calculation:
```python
def calculate_prs(surface_data, temporal_data, context_data):
    # Multi-dimensional quality assessment
    technical_score = assess_technical_quality(surface_data)
    visibility_score = assess_visibility(surface_data, context_data) 
    temporal_score = assess_temporal_stability(temporal_data)
    spatial_score = assess_spatial_suitability(surface_data)
    brand_safety_score = assess_brand_safety(context_data)
    
    # Weighted combination
    prs = (
        technical_score * 0.25 +
        visibility_score * 0.25 +
        temporal_score * 0.20 + 
        spatial_score * 0.20 +
        brand_safety_score * 0.10
    )
    
    return prs
```

#### Key Data Structures:
```json
{
  "placement_id": "place_001",
  "surface_id": "surface_001", 
  "prs_components": {
    "technical_score": 85.2,
    "visibility_score": 90.1,
    "temporal_score": 82.7,
    "spatial_score": 88.9,
    "brand_safety_score": 95.0,
    "final_prs": 87.5
  },
  "compositing_metadata": {
    "transform_matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "blend_mode": "normal",
    "opacity": 0.9
  },
  "quality_check": {
    "passed": true,
    "warnings": [],
    "blockers": []
  }
}
```

### Stage 5: MEASURE
**Input**: Placement opportunities with quality scores  
**Output**: Analytics, metrics, and performance data

#### Sequence:
1. **PRS Analytics**
   ```
   PRS Scores → Trend Analysis → Quality Metrics → Performance Dashboard
   ```

2. **Exposure Geometry**
   ```
   Placement Data → Viewing Angle Analysis → Visibility Calculation → Attention Metrics
   ```

3. **Business Intelligence**
   ```
   Quality Metrics → Revenue Attribution → ROI Analysis → Business Dashboard
   ```

#### Key Metrics:
- **Quality Metrics**: PRS distribution, improvement trends, failure analysis
- **Performance Metrics**: Processing latency, throughput, accuracy
- **Business Metrics**: Revenue per placement, CPM optimization, fill rates

### Stage 6: EVENTS
**Input**: System metrics and placement data  
**Output**: Event streams for real-time monitoring and external systems

#### Sequence:
1. **Event Generation**
   ```
   System State → Event Creation → Schema Validation → Event Queue
   ```

2. **Stream Processing**
   ```
   Event Queue → Stream Processor → Real-time Analytics → Alert Generation
   ```

3. **External Integration**
   ```
   Event Streams → API Gateway → External Systems → Webhook Delivery
   ```

#### Event Types:
```json
{
  "event_type": "placement_opportunity_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "content_id": "content_123",
  "opportunity_id": "opp_456", 
  "prs_score": 87.5,
  "surface_type": "wall",
  "metadata": {...}
}
```

### Stage 7: DELIVERY
**Input**: Packaged sidecar metadata and placement opportunities  
**Output**: Distribution-ready content for streaming platforms and CDNs

#### Sequence:
1. **Packaging**
   ```
   Placement Data → Sidecar Creation → Format Conversion → Validation
   ```

2. **Distribution**
   ```
   Sidecar Files → CDN Upload → Cache Distribution → API Endpoints
   ```

3. **Real-time Serving**
   ```
   API Requests → Cache Lookup → Data Serving → Response Delivery
   ```

## Data Storage Architecture

### Primary Storage
- **PostgreSQL**: Structured metadata, scene graphs, analytics
- **Object Storage**: Video content, depth maps, sidecar files
- **Redis**: Caching, session data, real-time metrics
- **Blockchain Ledger**: Rights management, audit trails

### Data Partitioning
```sql
-- Partition by content ingestion date for performance
CREATE TABLE scene_graphs (
    id UUID PRIMARY KEY,
    content_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    data JSONB NOT NULL
) PARTITION BY RANGE (created_at);

-- Time-based partitions
CREATE TABLE scene_graphs_2024_01 PARTITION OF scene_graphs 
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Data Retention
- **Raw Content**: 90 days (configurable per rights agreement)
- **Perception Data**: 30 days (compressed after processing)
- **Scene Graphs**: 1 year (archived to cold storage)
- **Analytics**: 3 years (aggregated for long-term trends)
- **Audit Trails**: 7 years (regulatory compliance)

## Performance Characteristics

### Throughput
- **Ingestion**: 100 GB/hour sustained
- **Perception**: 30 FPS real-time, 300 FPS batch
- **SGI**: 10 scene graphs/second
- **Rendering**: 50 placements/second

### Latency
- **End-to-end Pipeline**: <5 minutes for standard content
- **Real-time Processing**: <100ms for edge scenarios
- **API Response**: <50ms for cached data
- **Event Processing**: <10ms for real-time events

### Scalability
- **Horizontal Scaling**: Auto-scaling based on queue depth
- **Load Balancing**: Round-robin with sticky sessions
- **Cache Strategy**: Multi-tier caching (Redis, CDN, browser)
- **Database Scaling**: Read replicas, connection pooling

## Data Quality & Validation

### Input Validation
- Schema validation at each stage boundary
- Content integrity checks (checksums, format validation)
- Metadata consistency validation
- Rights chain verification

### Data Lineage
- Full traceability from input to output
- Processing step documentation
- Quality score attribution
- Error propagation tracking

### Quality Metrics
- Data completeness percentage
- Processing accuracy metrics
- Error rate monitoring
- Performance degradation alerts

## Security & Privacy

### Data Protection
- Encryption at rest and in transit
- PII identification and anonymization
- Secure multi-tenant data isolation
- GDPR/CCPA compliance workflows

### Access Control
- Role-based access control (RBAC)
- API key management and rotation
- Audit logging for all data access
- Data export controls for sensitive content

---

**Document Version**: 2.0  
**Last Updated**: January 2024  
**Next Review**: April 2024