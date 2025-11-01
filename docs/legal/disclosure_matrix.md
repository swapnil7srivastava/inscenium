# Disclosure Requirements Matrix

## Global Jurisdiction Overview

This matrix outlines disclosure requirements for dynamic product placement across major regulatory jurisdictions. **TODO: Consult legal counsel for specific compliance requirements in each jurisdiction.**

| Jurisdiction | Regulatory Body | Primary Regulation | Disclosure Requirements | Timing Requirements |
|-------------|----------------|-------------------|----------------------|-------------------|
| United States | FTC | FTC Act Section 5 | Clear & conspicuous disclosure | Before placement exposure |
| India | ASCI | Code for Commercial Communications | Sponsored content labeling | Real-time or pre-roll |
| United Kingdom | Ofcom | Broadcasting Code | Product placement notification | Beginning/end of program |
| European Union | AVMSD | Audiovisual Media Services Directive | "PP" symbol or equivalent | During placement window |

## Detailed Requirements by Jurisdiction

### United States - FTC Guidelines
- **Standard**: "Clear and conspicuous" disclosure
- **Dynamic Placement**: Must disclose relationship between advertiser and content
- **Trigger Events**: Any material connection between advertiser and content creator
- **Format**: Text overlay, audio disclosure, or visual indicator
- **Duration**: Sufficient time for average viewer to notice and understand
- **Language**: Native language of content or English

**TODO**: Verify specific requirements for AI-generated placement disclosure.

### India - ASCI Code
- **Standard**: Must be "upfront and unmistakable"
- **Dynamic Placement**: Label as "sponsored" or "paid promotion"
- **Trigger Events**: Any commercial communication or promotion
- **Format**: Text overlay in local language preferred
- **Duration**: Minimum 3 seconds for video content
- **Language**: Hindi, English, or regional language of content

**TODO**: Confirm ASCI guidelines for retrospective placement in existing content.

### United Kingdom - Ofcom Broadcasting Code
- **Standard**: Audience must be made aware of product placement
- **Dynamic Placement**: "PP" symbol or textual disclosure
- **Trigger Events**: Paid product placement in broadcast content
- **Format**: Visual "PP" logo or equivalent
- **Duration**: 3 seconds minimum at program start/end
- **Language**: English or Welsh as appropriate

**TODO**: Clarify requirements for streaming vs. broadcast content.

### European Union - AVMSD
- **Standard**: Transparency and consumer protection
- **Dynamic Placement**: Neutral logo or symbol indicating placement
- **Trigger Events**: Product placement in audiovisual media services
- **Format**: Standardized "PP" symbol or member state equivalent
- **Duration**: Beginning and end of program, after commercial breaks
- **Language**: Member state official language(s)

**TODO**: Review individual member state implementations.

## Implementation Matrix for Inscenium

### Automatic Detection Triggers
| Content Type | Trigger Logic | Disclosure Method | Compliance Check |
|-------------|---------------|------------------|------------------|
| Brand Logo | Computer vision detection | Text overlay + duration | FTC/ASCI compliant |
| Product Placement | Object recognition + rights ledger | Standard PP symbol | AVMSD compliant |
| Sponsored Content | Rights metadata flag | Audio + visual disclosure | Multi-jurisdiction |
| Influencer Content | Creator relationship data | "Paid Partnership" overlay | Platform-specific |

### Technical Implementation

```
Dynamic Disclosure Pipeline:
1. Content Analysis → 2. Jurisdiction Detection → 3. Requirement Lookup → 4. Disclosure Generation
```

**Jurisdiction Detection Logic:**
- IP geolocation for viewer
- Content origin metadata  
- Platform distribution rights
- User account preferences

**Disclosure Generation:**
- Template-based system per jurisdiction
- Multi-language support
- Accessibility compliance (WCAG 2.1)
- Platform-specific formatting

## Risk Assessment

### High Risk Scenarios
- Cross-border streaming without proper disclosure
- Retrospective placement in archived content
- AI-generated content without clear attribution
- Children's content with commercial elements

**TODO**: Develop risk mitigation strategies for each scenario.

### Compliance Monitoring
- Real-time disclosure verification
- Audit trail for all placement decisions
- User complaint handling system
- Regulatory reporting capabilities

**TODO**: Integrate with content monitoring systems.

## Action Items

### Legal Review Required
- [ ] Consult FTC legal counsel on AI placement disclosure
- [ ] Review GDPR implications for user data in targeting
- [ ] Confirm children's content restrictions (COPPA/GDPR-K)
- [ ] Validate accessibility requirements (ADA/EAA)

### Technical Implementation
- [ ] Build jurisdiction detection system
- [ ] Create disclosure template library
- [ ] Implement real-time compliance checking
- [ ] Develop audit logging for regulatory requests

### Content Policy
- [ ] Define prohibited content categories
- [ ] Create brand safety guidelines
- [ ] Establish age-appropriate placement rules
- [ ] Document editorial vs. advertising boundaries

## Updates and Maintenance

This matrix requires regular updates as regulations evolve:

- **Quarterly**: Review regulatory updates from each jurisdiction
- **Annually**: Full legal compliance audit
- **As needed**: Updates for new markets or platforms

**Last Updated**: [TODO: Insert current date]
**Next Review**: [TODO: Insert quarterly review date]

---

**Disclaimer**: This matrix is for informational purposes only and does not constitute legal advice. Consult qualified legal counsel for specific compliance requirements.