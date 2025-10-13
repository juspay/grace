"""Research workflow using LangGraph for intelligent research automation."""

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import re
from langgraph.graph import StateGraph, START, END


class ResearchWorkflowState(TypedDict):
    """State container for the research workflow."""
    query: str
    analyzed_query: Optional[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]]
    extracted_content: Optional[List[Dict[str, Any]]]
    analysis_results: Optional[Dict[str, Any]]
    synthesized_report: str
    formatted_output: str
    format_type: str
    depth: int
    max_sources: int
    error: Optional[str]
    metadata: Dict[str, Any]


class ResearchWorkflow:
    """LangGraph-based research workflow orchestrator."""

    def __init__(self):
        """Initialize the research workflow."""
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self):
        """Build the LangGraph workflow graph."""

        # Create state graph
        workflow = StateGraph(ResearchWorkflowState)

        # Add nodes for each step
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("discover_sources", self._discover_sources)
        workflow.add_node("extract_content", self._extract_content)
        workflow.add_node("analyze_content", self._analyze_content)
        workflow.add_node("synthesize_report", self._synthesize_report)
        workflow.add_node("format_output", self._format_output)

        # Add edges to define workflow flow
        workflow.add_edge(START, "analyze_query")
        workflow.add_edge("analyze_query", "discover_sources")
        workflow.add_edge("discover_sources", "extract_content")
        workflow.add_edge("extract_content", "analyze_content")
        workflow.add_edge("analyze_content", "synthesize_report")
        workflow.add_edge("synthesize_report", "format_output")
        workflow.add_edge("format_output", END)

        # Compile the graph
        return workflow.compile()

    def _analyze_query(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Analyze the research query to understand intent and scope."""
        try:
            # Analyze query characteristics
            analyzed_query = {
                "intent": "research",
                "domain": self._extract_domain(state["query"]),
                "keywords": self._extract_keywords(state["query"]),
                "scope": "comprehensive" if state["depth"] > 7 else "focused",
                "complexity": "high" if len(state["query"].split()) > 10 else "medium",
                "query_length": len(state["query"]),
                "word_count": len(state["query"].split())
            }

            state["analyzed_query"] = analyzed_query
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"].update({"step": "query_analysis", "status": "completed"})

        except Exception as e:
            state["error"] = f"Query analysis failed: {str(e)}"

        return state

    def _discover_sources(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Discover relevant sources for the research query."""
        try:
            # Mock implementation - in real scenario, integrate with search APIs
            # Google Scholar, arXiv, academic databases, news APIs, etc.

            analyzed_query = state["analyzed_query"]
            if analyzed_query is None:
                raise ValueError("Analyzed query is required but was None")

            domain = analyzed_query["domain"]
            keywords = analyzed_query["keywords"]

            sources = []
            source_types = ["academic_paper", "news_article", "blog_post", "documentation", "forum_discussion"]

            for i in range(min(state["max_sources"], 15)):
                source_type = source_types[i % len(source_types)]
                sources.append({
                    "id": f"source_{i}",
                    "url": f"https://example.com/{domain}/source_{i}",
                    "title": f"{keywords[0] if keywords else 'Research'} Study {i+1}: {state['query'][:50]}...",
                    "relevance_score": max(0.1, 0.95 - (i * 0.06)),
                    "source_type": source_type,
                    "domain": domain,
                    "publication_date": "2024-01-01",
                    "author": f"Author {i+1}",
                    "abstract": f"Abstract for source {i+1} related to {state['query'][:100]}...",
                    "citation_count": max(0, 100 - i * 10),
                    "quality_score": max(0.1, 0.9 - (i * 0.05))
                })

            # Sort by relevance and quality
            sources.sort(key=lambda x: x["relevance_score"] * x["quality_score"], reverse=True)

            state["sources"] = sources[:state["max_sources"]]
            state["metadata"].update({
                "sources_found": len(sources),
                "sources_selected": len(state["sources"])
            })

        except Exception as e:
            state["error"] = f"Source discovery failed: {str(e)}"

        return state

    def _extract_content(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Extract content from discovered sources."""
        try:
            sources = state["sources"]
            if sources is None:
                raise ValueError("Sources are required but were None")

            extracted_content = []

            for i, source in enumerate(sources):
                # Mock content extraction - in real scenario, use web scraping,
                # PDF parsing, API calls to academic databases, etc.

                content_length = max(200, 1000 - i * 50)  # Varying content lengths
                analyzed_query = state.get("analyzed_query", {})

                content = {
                    "source_id": source["id"],
                    "source_url": source["url"],
                    "title": source["title"],
                    "content": f"""
This is extracted content from {source['title']}.

Key findings related to {state['query']}:
1. Finding number one about the research topic with detailed analysis.
2. Second important finding that provides insights into the subject matter.
3. Third finding that connects to broader implications and applications.

The content discusses various aspects of {analyzed_query.get('keywords', [{}])[0] if analyzed_query and analyzed_query.get('keywords') else 'the topic'}
and provides comprehensive coverage of the subject matter with evidence-based conclusions.

Methodology used in this source includes both quantitative and qualitative analysis
approaches that strengthen the validity of the findings presented.
                    """.strip(),
                    "summary": f"Comprehensive analysis of {source['title']} covering key aspects of {state['query'][:50]}",
                    "key_points": [
                        f"Primary insight from {source['title']}: {analyzed_query.get('keywords', ['topic'])[0] if analyzed_query and analyzed_query.get('keywords') else 'topic'} analysis",
                        f"Secondary finding: methodology and approach discussion",
                        f"Tertiary conclusion: implications and future research directions",
                        f"Supporting evidence: data validation and peer review insights"
                    ],
                    "extraction_metadata": {
                        "word_count": content_length,
                        "extraction_quality": "high" if source["quality_score"] > 0.7 else "medium",
                        "content_type": source["source_type"],
                        "extraction_method": "web_scraping" if "http" in source["url"] else "api",
                        "language": "en"
                    },
                    "citations": [
                        f"Citation 1 from {source['title']}",
                        f"Citation 2 from {source['title']}"
                    ]
                }
                extracted_content.append(content)

            state["extracted_content"] = extracted_content
            state["metadata"].update({
                "content_extracted": len(extracted_content),
                "total_word_count": sum(c["extraction_metadata"]["word_count"] for c in extracted_content)
            })

        except Exception as e:
            state["error"] = f"Content extraction failed: {str(e)}"

        return state

    def _analyze_content(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Analyze extracted content for insights and patterns."""
        try:
            # Mock analysis - in real scenario, use NLP, sentiment analysis,
            # topic modeling, entity extraction, etc.

            extracted_content = state["extracted_content"]
            if extracted_content is None:
                raise ValueError("Extracted content is required but was None")

            analyzed_query = state["analyzed_query"]
            if analyzed_query is None:
                raise ValueError("Analyzed query is required but was None")

            all_content = " ".join([c["content"] for c in extracted_content])
            keywords = analyzed_query["keywords"]

            # Simulate theme extraction
            themes = [
                f"Primary theme: {keywords[0] if keywords else 'Main topic'} fundamentals and core concepts",
                f"Secondary theme: Methodological approaches and best practices",
                f"Tertiary theme: Future directions and emerging trends",
                f"Cross-cutting theme: Practical applications and real-world implementations"
            ]

            # Simulate insight generation
            insights = [
                f"Key insight 1: {state['query'][:30]}... shows significant implications for the field",
                f"Key insight 2: Multiple sources converge on the importance of methodological rigor",
                f"Key insight 3: Emerging trends suggest new directions for future research",
                f"Key insight 4: Practical applications demonstrate real-world value and impact",
                f"Key insight 5: Cross-disciplinary connections reveal broader significance"
            ]

            # Simulate contradiction detection
            contradictions = []
            if len(state["extracted_content"]) > 3:
                contradictions = [
                    "Minor methodological differences in data collection approaches",
                    "Varying sample sizes across studies may affect generalizability"
                ]

            analysis_results = {
                "main_themes": themes,
                "key_insights": insights,
                "contradictions": contradictions,
                "confidence_level": "high" if len(state["extracted_content"]) >= 5 else "medium",
                "data_quality": "excellent" if state["metadata"]["total_word_count"] > 3000 else "good",
                "gaps_identified": [
                    "Limited longitudinal studies in the reviewed literature",
                    "Need for more diverse participant demographics",
                    "Opportunity for cross-cultural validation studies"
                ],
                "sentiment_analysis": {
                    "overall_sentiment": "positive",
                    "confidence_scores": {"positive": 0.7, "neutral": 0.25, "negative": 0.05}
                },
                "entity_analysis": {
                    "key_entities": keywords[:5] if keywords else ["research", "analysis", "study"],
                    "entity_frequency": {kw: len(all_content.lower().split(kw.lower())) - 1 for kw in keywords[:3]} if keywords else {}
                }
            }

            state["analysis_results"] = analysis_results
            state["metadata"].update({
                "analysis_completed": True,
                "themes_identified": len(themes),
                "insights_generated": len(insights)
            })

        except Exception as e:
            state["error"] = f"Content analysis failed: {str(e)}"

        return state

    def _synthesize_report(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Synthesize findings into a coherent research report."""
        try:
            extracted_content = state.get("extracted_content", [])
            analysis_results = state.get("analysis_results", {})
            analyzed_query = state.get("analyzed_query", {})
            sources = state.get("sources", [])

            if not extracted_content:
                raise ValueError("Extracted content is required but was empty")
            if not analysis_results:
                raise ValueError("Analysis results are required but were empty")

            # Create comprehensive report structure
            report_sections = {
                "executive_summary": f"""
This research investigation explores {state['query']} through comprehensive analysis of {len(extracted_content)} high-quality sources.
The study reveals {len(analysis_results.get('key_insights', []))} key insights with {analysis_results.get('confidence_level', 'unknown')} confidence level.
Primary findings indicate significant implications for both theoretical understanding and practical applications in the field.
                """.strip(),

                "methodology": f"""
Research methodology employed a multi-source approach analyzing {state['metadata'].get('sources_found', 0)} initial sources,
selecting {state['metadata'].get('sources_selected', 0)} highest-quality sources for detailed content extraction.
Analysis depth was set to level {state['depth']} ensuring {analyzed_query.get('scope', 'focused')} coverage.
Content analysis utilized advanced NLP techniques for theme identification, insight extraction, and quality assessment.
                """.strip(),

                "findings": analysis_results.get("key_insights", []),
                "themes": analysis_results.get("main_themes", []),

                "conclusions": f"""
The research demonstrates clear convergence around key themes with {analysis_results.get('confidence_level', 'unknown')} confidence.
Analysis reveals {len(analysis_results.get('key_insights', []))} primary insights that advance understanding of {state['query'][:50]}{'...' if len(state['query']) > 50 else ''}.
Data quality assessment indicates {analysis_results.get('data_quality', 'unknown')} overall source reliability and comprehensive coverage.
                """.strip(),

                "recommendations": f"""
Based on the comprehensive analysis, we recommend:
1. Further investigation into the {analysis_results.get('gaps_identified', ['identified research gaps'])[0] if analysis_results.get('gaps_identified') else 'identified research gaps'}
2. Implementation of findings in practical applications where appropriate
3. Continued monitoring of emerging trends and developments in this area
4. Cross-validation of results through additional methodological approaches
                """.strip(),

                "limitations": f"""
This research has several limitations to consider:
1. Analysis based on {len(extracted_content)} sources may not capture all perspectives
2. {', '.join(analysis_results.get('contradictions', [])) if analysis_results.get('contradictions') else 'No significant contradictions identified, but broader validation recommended'}
3. Temporal constraints may limit coverage of most recent developments
4. Language limitations may exclude non-English sources
                """.strip(),

                "sources": [{"title": source["title"], "url": source["url"], "type": source["source_type"]} for source in sources]
            }

            # Create structured report
            synthesized_report = self._create_report_structure(report_sections, state["query"])
            state["synthesized_report"] = synthesized_report
            state["metadata"].update({
                "synthesis_completed": True,
                "report_word_count": len(synthesized_report.split()),
                "report_sections": len(report_sections)
            })

        except Exception as e:
            state["error"] = f"Report synthesis failed: {str(e)}"

        return state

    def _format_output(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Format the synthesized report according to specified format."""
        try:
            if state["format_type"] == "markdown":
                formatted_output = self._format_markdown(state["synthesized_report"])
            elif state["format_type"] == "json":
                formatted_output = self._format_json(state)
            elif state["format_type"] == "text":
                formatted_output = self._format_text(state["synthesized_report"])
            else:
                formatted_output = state["synthesized_report"]

            state["formatted_output"] = formatted_output
            state["metadata"].update({
                "formatting_completed": True,
                "final_format": state["format_type"],
                "output_length": len(formatted_output)
            })

        except Exception as e:
            state["error"] = f"Output formatting failed: {str(e)}"

        return state

    # Helper methods
    def _extract_domain(self, query: str) -> str:
        """Extract domain from query."""
        tech_keywords = ["AI", "machine learning", "software", "technology", "programming", "algorithm", "data science", "computer"]
        business_keywords = ["business", "market", "strategy", "finance", "economics", "management", "startup", "investment"]
        science_keywords = ["research", "study", "analysis", "experiment", "hypothesis", "methodology", "clinical", "scientific"]

        query_lower = query.lower()
        if any(keyword.lower() in query_lower for keyword in tech_keywords):
            return "technology"
        elif any(keyword.lower() in query_lower for keyword in business_keywords):
            return "business"
        elif any(keyword.lower() in query_lower for keyword in science_keywords):
            return "science"
        else:
            return "general"

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "is", "at", "which", "on", "and", "a", "to", "for", "of", "with", "as",
            "in", "by", "from", "up", "about", "into", "through", "during", "before",
            "after", "above", "below", "between", "among", "an", "but", "or", "because",
            "while", "where", "when", "who", "what", "how", "why", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "am", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can"
        }

        # Clean and split query
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords = [word for word in words if word not in stop_words]

        # Return unique keywords, preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords[:10]  # Return top 10 keywords

    def _create_report_structure(self, sections: Dict[str, Any], query: str) -> str:
        """Create structured report content."""
        report = f"""# Research Report: {query}

## Executive Summary
{sections['executive_summary']}

## Methodology
{sections['methodology']}

## Key Findings
"""
        for i, finding in enumerate(sections['findings'], 1):
            report += f"{i}. {finding}\n"

        report += f"""
## Main Themes
"""
        for i, theme in enumerate(sections['themes'], 1):
            report += f"{i}. {theme}\n"

        report += f"""
## Conclusions
{sections['conclusions']}

## Recommendations
{sections['recommendations']}

## Limitations
{sections['limitations']}

## Sources ({len(sections['sources'])})
"""
        for i, source in enumerate(sections['sources'], 1):
            report += f"{i}. **{source['title']}** ({source['type']})  \n   {source['url']}\n\n"

        # Add metadata footer
        report += f"""
---
*Report generated using automated research workflow*
*Analysis confidence: {sections.get('confidence_level', 'medium')}*
*Sources analyzed: {len(sections['sources'])}*
"""
        return report

    def _format_markdown(self, content: str) -> str:
        """Format content as markdown."""
        return content  # Already in markdown format

    def _format_json(self, state: ResearchWorkflowState) -> str:
        """Format content as JSON."""
        output = {
            "query": state["query"],
            "analysis": state["analysis_results"],
            "report": state["synthesized_report"],
            "sources": state["sources"],
            "metadata": state["metadata"],
            "format": "json",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        return json.dumps(output, indent=2, ensure_ascii=False)

    def _format_text(self, content: str) -> str:
        """Format content as plain text."""
        # Remove markdown formatting
        text = re.sub(r'#{1,6}\s*', '', content)  # Remove headers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Remove italic
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Remove links
        text = re.sub(r'\n{3,}', '\n\n', text)  # Normalize line breaks
        return text.strip()

    async def execute(self,
                     query: str,
                     format_type: str = "markdown",
                     depth: int = 5) -> Dict[str, Any]:
        """Execute the research workflow."""

        # Initialize state
        initial_state: ResearchWorkflowState = {
            "query": query,
            "analyzed_query": None,
            "sources": None,
            "extracted_content": None,
            "analysis_results": None,
            "synthesized_report": "",
            "formatted_output": "",
            "format_type": format_type,
            "depth": depth,
            "max_sources": 10, #need to change to .env
            "error": None,
            "metadata": {"workflow_started": True, "timestamp": "2024-01-01T00:00:00Z"}
        }

        try:
            # Execute the workflow graph
            result = await self.graph.ainvoke(initial_state)

            return {
                "success": result["error"] is None,
                "query": result["query"],
                "output": result["formatted_output"],
                "metadata": result["metadata"],
                "error": result["error"],
                "sources_count": len(result["sources"]) if result["sources"] else 0,
                "analysis_confidence": result["analysis_results"]["confidence_level"] if result["analysis_results"] else "unknown"
            }

        except Exception as e:
            return {
                "success": False,
                "query": query,
                "output": "",
                "metadata": {"error": str(e), "workflow_failed": True},
                "error": str(e),
                "sources_count": 0,
                "analysis_confidence": "unknown"
            }


# Factory function for easy workflow creation
def create_research_workflow() -> ResearchWorkflow:
    """Create and return a new research workflow instance."""
    return ResearchWorkflow()


# CLI integration function
async def run_research_workflow(query: str,
                               format_type: str = "markdown",
                               depth: int = 5) -> Dict[str, Any]:
    """Run research workflow from CLI."""
    workflow = create_research_workflow()
    return await workflow.execute(query, format_type, depth)