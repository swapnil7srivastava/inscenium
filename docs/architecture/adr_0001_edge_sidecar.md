# ADR-0001: Edge Sidecar Architecture Decision

## Status
**Accepted** - January 15, 2024

## Context

Inscenium needs to deliver placement opportunities to edge devices and streaming platforms in real-time scenarios. We evaluated two primary approaches:

1. **HLS Sidecars with Timed Metadata** - Embed placement data as timed metadata in HLS streams
2. **Alternative Clip Replacement** - Replace video segments with placement-composited versions

This decision is critical for:
- Real-time placement delivery performance
- Compatibility with existing streaming infrastructure  
- Edge device processing capabilities
- Content delivery network (CDN) integration
- Regulatory compliance and disclosure requirements

## Decision

**We will implement HLS Sidecars with Timed Metadata as the primary edge delivery mechanism.**

## Rationale

### HLS Sidecars Advantages

#### 1. **Real-Time Flexibility**
- Dynamic placement decisions without pre-rendering all variants
- Ability to adapt to viewer context (location, device, preferences)
- A/B testing capabilities for placement optimization
- Revenue optimization through real-time bidding integration

#### 2. **Infrastructure Compatibility**
- Leverages existing HLS streaming infrastructure
- Compatible with all major CDNs (CloudFront, Cloudflare, Fastly)
- Works with standard HLS players (Video.js, HLS.js, native players)
- No special server-side compositing requirements

#### 3. **Bandwidth Efficiency**
- Single video stream + lightweight metadata (typically <10KB per segment)
- No need to store multiple pre-rendered placement variants
- Reduced CDN storage costs and cache efficiency
- Lower bandwidth requirements compared to multiple video streams

#### 4. **Edge Processing Capabilities**
- Client-side compositing using WebGL/WebAssembly
- GPU acceleration on modern devices
- Progressive enhancement (fallback to no placement on older devices)
- Local processing reduces privacy concerns

#### 5. **Regulatory Compliance**
- Real-time disclosure generation based on viewer jurisdiction
- Dynamic adaptation to local advertising regulations
- Audit trail for placement decisions and disclosure delivery
- Content rating integration (MPAA, BBFC, etc.)

### Technical Implementation

#### HLS Manifest Structure
```m3u8
#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:10

#EXT-X-DATERANGE:ID="placement_001",START-DATE="2024-01-15T10:30:00Z",DURATION=5.0,X-INSCENIUM-SURFACE-ID="surf_001",X-INSCENIUM-PRS="87.5",X-INSCENIUM-PLACEMENT-TYPE="billboard"
#EXTINF:10.0,
segment_001.m4s

#EXT-X-DATERANGE:ID="placement_002",START-DATE="2024-01-15T10:35:00Z",DURATION=3.2,X-INSCENIUM-SURFACE-ID="surf_002",X-INSCENIUM-PRS="92.1",X-INSCENIUM-PLACEMENT-TYPE="screen"
#EXTINF:10.0,
segment_002.m4s
```

#### Metadata Schema
```json
{
  "placement_id": "placement_001",
  "surface_id": "surf_001", 
  "start_time": 42.5,
  "duration": 5.0,
  "prs_score": 87.5,
  "placement_type": "billboard",
  "surface_geometry": {
    "coordinates": [[100, 150], [400, 150], [400, 300], [100, 300]],
    "transform_matrix": [[1.2, 0.1, 50], [0, 1.1, 30], [0, 0, 1]]
  },
  "content_reference": {
    "creative_url": "https://cdn.example.com/creative_12345.png",
    "creative_size": [300, 250],
    "creative_format": "png"
  },
  "disclosure": {
    "required": true,
    "text": "Paid Partnership",
    "duration": 3.0,
    "jurisdiction": "US"
  },
  "brand_safety": {
    "score": 95.2,
    "categories": ["safe_content", "brand_suitable"],
    "restrictions": []
  }
}
```

#### Edge Processing Pipeline
```javascript
// WebAssembly-based compositing engine
class InsceniumPlayer {
  constructor(videoElement, wasmModule) {
    this.video = videoElement;
    this.compositor = new WasmCompositor(wasmModule);
    this.placementQueue = [];
  }
  
  onTimedMetadata(metadata) {
    const placement = this.parseInsceniumMetadata(metadata);
    if (this.canComposite(placement)) {
      this.placementQueue.push(placement);
    }
  }
  
  onFrame(canvas, timestamp) {
    const activePlacements = this.getActivePlacements(timestamp);
    this.compositor.compositeFrame(canvas, activePlacements);
  }
}
```

### Alternative Clip Replacement - Rejected

#### Rejection Reasons

1. **Storage Overhead**
   - Exponential growth in storage requirements (N variants × M placements)
   - CDN cache inefficiency due to content multiplication
   - Higher bandwidth costs for content delivery

2. **Reduced Flexibility** 
   - Pre-rendering limits real-time optimization
   - Difficult to implement A/B testing
   - No viewer-specific customization capabilities
   - Challenging personalization based on user data

3. **Infrastructure Complexity**
   - Requires sophisticated server-side segment switching
   - Complex cache invalidation strategies
   - Increased CDN configuration complexity
   - Higher operational overhead

4. **Technical Limitations**
   - Segment boundary alignment challenges
   - Audio continuity issues during switching
   - Potential quality degradation from re-encoding
   - Limited placement duration flexibility

## Implementation Plan

### Phase 1: Core Infrastructure (Month 1-2)
- [ ] HLS manifest parsing and metadata injection
- [ ] Basic WebAssembly compositor for edge devices
- [ ] Placement geometry and transform calculations
- [ ] Simple disclosure overlay system

### Phase 2: Advanced Features (Month 3-4)
- [ ] GPU-accelerated compositing (WebGL)
- [ ] Advanced blend modes and visual effects
- [ ] Real-time quality adaptation based on device capabilities
- [ ] Comprehensive error handling and fallback mechanisms

### Phase 3: Production Optimization (Month 5-6)
- [ ] CDN integration and cache optimization
- [ ] Performance monitoring and analytics
- [ ] A/B testing framework integration
- [ ] Regulatory compliance automation

### Phase 4: Enterprise Features (Month 7+)
- [ ] Multi-jurisdiction compliance automation
- [ ] Advanced brand safety filtering
- [ ] Real-time bidding integration
- [ ] Advanced analytics and reporting

## Consequences

### Positive
- **Scalable Architecture**: Handles millions of concurrent viewers
- **Real-Time Optimization**: Dynamic placement decisions improve revenue
- **Future-Proof**: Compatible with emerging streaming standards
- **Cost Efficiency**: Lower storage and bandwidth requirements
- **Developer Experience**: Standard HLS tools and workflows

### Negative
- **Client Complexity**: Requires sophisticated edge processing capabilities
- **Device Compatibility**: Limited by client-side compositing support
- **Fallback Strategy**: Need graceful degradation for unsupported devices
- **Testing Complexity**: More complex QA across diverse device ecosystem

### Risk Mitigation
- **Progressive Enhancement**: Core functionality works without placement, enhanced experience with compositing
- **Comprehensive Testing**: Device compatibility matrix and automated testing
- **Performance Monitoring**: Real-time metrics for compositing performance
- **Fallback Mechanisms**: Server-side compositing for critical use cases

## Compliance Considerations

### Privacy
- Client-side processing keeps viewer data local
- Placement decisions can be made without server round-trips
- GDPR compliance through local data processing

### Accessibility
- Placement disclosure integration with screen readers
- High contrast mode support for visual impairments
- Keyboard navigation compatibility

### Regional Regulations
- Dynamic disclosure text based on viewer location
- Content rating integration for age-appropriate placement
- Real-time compliance checking and enforcement

## Monitoring and Success Metrics

### Technical Metrics
- **Compositing Performance**: Frame rate impact, battery usage
- **Error Rates**: Failed placements, unsupported devices
- **Cache Hit Rates**: CDN efficiency, bandwidth usage

### Business Metrics  
- **Fill Rates**: Percentage of opportunities successfully filled
- **Revenue Per Viewer**: Optimization through real-time decisions
- **User Experience**: Viewing time, engagement metrics

### Quality Metrics
- **Placement Quality**: Visual integration, brand safety scores
- **Disclosure Compliance**: Regulatory requirement adherence
- **Content Integrity**: Viewer experience impact assessment

## References

- [HLS Specification RFC 8216](https://tools.ietf.org/html/rfc8216)
- [WebAssembly Streaming Compilation](https://webassembly.org/docs/web/#streaming-compilation)
- [FTC Disclosure Guidelines](https://www.ftc.gov/tips-advice/business-center/guidance/ftcs-endorsement-guides-what-people-are-asking)
- [WebGL 2.0 Specification](https://www.khronos.org/registry/webgl/specs/latest/2.0/)

---

**Decision Made By**: Technical Architecture Team  
**Reviewed By**: Engineering, Product, Legal  
**Next Review**: July 2024 (6 months)

**Supersedes**: N/A  
**Superseded By**: N/A