"""Draft mode pipeline - generates editable wireframe diagrams."""

import json
import re
from typing import AsyncGenerator, Optional, Dict, Any

from app.services.pipeline.base import BasePipeline, PipelineContext, PipelineResult


class DraftPipeline(BasePipeline):
    """Draft mode: Generate editable draw.io XML diagrams.
    
    Steps:
    1. Analyze user prompt
    2. Generate structure plan
    3. Generate draw.io XML
    """
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute draft pipeline."""
        try:
            # Step 1: Generate plan
            plan = await self._generate_plan(context)
            
            # Step 2: Generate XML
            xml_content = await self._generate_xml(context, plan)
            
            return PipelineResult(
                success=True,
                message="Draft generated successfully",
                data={
                    "xml": xml_content,
                    "plan": plan,
                    "mode": "draft"
                }
            )
        except Exception as e:
            import traceback
            print(f"Draft pipeline error: {e}")
            print(traceback.format_exc())
            return PipelineResult(
                success=False,
                message=f"Draft generation failed: {str(e)}"
            )
    
    async def execute_stream(self, context: PipelineContext) -> AsyncGenerator[str, None]:
        """Execute with streaming (for progress updates)."""
        yield json.dumps({"step": "planning", "message": "Analyzing requirements..."})
        
        try:
            plan = await self._generate_plan(context)
            yield json.dumps({"step": "planning_complete", "plan": plan})
            
            yield json.dumps({"step": "generating", "message": "Generating diagram..."})
            
            xml_content = await self._generate_xml(context, plan)
            yield json.dumps({
                "step": "complete",
                "xml": xml_content,
                "plan": plan,
                "mode": "draft"
            })
        except Exception as e:
            yield json.dumps({"step": "error", "message": str(e)})
    
    async def _generate_plan(self, context: PipelineContext) -> Dict[str, Any]:
        """Generate structure plan from prompt."""
        system_prompt = """你是一个流程图结构分析专家。分析用户的需求并输出结构化的流程图设计方案。

设计时必须达到以下质量基准（参考优秀学术论文插图样张）：
- 视觉质量：高分辨率、线条清晰锐利
- 信息密度：高密度但不拥挤，包含3-6个主要模块，每个模块有详细子组件
- 模块数量：丰富的节点和流程框图，模块间有清晰的连接关系和数据流
- 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等）
- 整体风格：学术论文图表风格，清晰的分块和边框
- 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
- 文字清晰度：所有标签必须清晰可读，字号层次分明

输出JSON格式：
{
    "title": "流程图标题",
    "nodes": [
        {"id": "1", "label": "节点名称", "type": "start|process|decision|end"}
    ],
    "edges": [
        {"from": "1", "to": "2", "label": "连接标签"}
    ],
    "layout": "horizontal|vertical",
    "style": "简洁描述风格"
}"""

        user_prompt = context.prompt
        if context.reference_image:
            ref_desc = await self._get_reference_analysis(context)
            if ref_desc:
                user_prompt = f"参考图片风格描述：{ref_desc}\n\n基于以上参考风格，{context.prompt}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm.chat_completion(
                messages,
                temperature=0.3,
            )
            
            content = await self.llm.extract_xml_from_response(response)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback: extract JSON from markdown
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                # Try to find any JSON-like structure
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Failed to parse plan JSON")
        except Exception as e:
            print(f"Plan generation error: {e}")
            # Return default plan
            return {
                "title": "流程图",
                "nodes": [
                    {"id": "1", "label": "开始", "type": "start"},
                    {"id": "2", "label": "处理", "type": "process"},
                    {"id": "3", "label": "结束", "type": "end"}
                ],
                "edges": [
                    {"from": "1", "to": "2", "label": ""},
                    {"from": "2", "to": "3", "label": ""}
                ],
                "layout": "horizontal",
                "style": "简洁风格"
            }
    
    async def _generate_xml(self, context: PipelineContext, plan: Dict[str, Any]) -> str:
        """Generate draw.io XML from plan."""
        system_prompt = """你是一个draw.io XML生成专家。根据提供的结构计划生成标准的mxGraph XML。

要求：
1. 使用标准的mxGraph格式
2. 节点使用mxCell with vertex="1"
3. 边使用mxCell with edge="1"
4. 使用合适的几何位置和大小
5. 包含样式属性（颜色、字体等）
6. 确保XML格式正确，可以直接在draw.io中打开
7. 质量基准（参考优秀学术论文插图样张）：
   - 视觉质量：高分辨率、线条清晰锐利
   - 信息密度：高密度但不拥挤，包含3-6个主要模块
   - 模块数量：丰富的节点和流程框图，模块间有清晰的连接关系
   - 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等）
   - 整体风格：学术论文图表风格，清晰的分块和边框
   - 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
   - 文字清晰度：所有标签必须清晰可读，字号层次分明

直接返回XML内容，格式如下：
<mxfile>
  <diagram>
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- 元素在这里 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

        plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
        user_prompt = f"根据以下结构计划生成draw.io XML：\n\n{plan_json}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm.chat_completion(
                messages,
                temperature=0.3,
            )
            
            xml_content = await self.llm.extract_xml_from_response(response)
            
            # Clean up XML
            xml_content = xml_content.strip()
            if xml_content.startswith("```xml"):
                xml_content = xml_content[7:]
            if xml_content.startswith("```"):
                xml_content = xml_content[3:]
            if xml_content.endswith("```"):
                xml_content = xml_content[:-3]
            
            result = xml_content.strip()
            
            # Validate XML
            if not result.startswith("<mxfile") and not result.startswith("<mxGraphModel"):
                # Wrap in mxfile if needed
                result = f"""<mxfile>
  <diagram name="Diagram">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {result}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
            
            return result
        except Exception as e:
            print(f"XML generation error: {e}")
            # Return default XML
            return self._generate_default_xml(plan)
    
    def _generate_default_xml(self, plan: Dict[str, Any]) -> str:
        """Generate default XML if LLM fails."""
        nodes = plan.get("nodes", [])
        edges = plan.get("edges", [])
        layout = plan.get("layout", "horizontal")
        
        # Calculate positions
        x_start = 100
        y_start = 100
        spacing = 200 if layout == "horizontal" else 100
        
        xml_elements = []
        
        for i, node in enumerate(nodes):
            node_id = node.get("id", str(i+1))
            label = node.get("label", f"Node {i+1}")
            node_type = node.get("type", "process")
            
            if layout == "horizontal":
                x = x_start + i * spacing
                y = y_start
            else:
                x = x_start
                y = y_start + i * spacing
            
            # Style based on type
            if node_type == "start":
                style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;"
            elif node_type == "end":
                style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;"
            elif node_type == "decision":
                style = "rhombus;whiteSpace=wrap;html=1;fillColor=#fff3e0;"
            else:
                style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;"
            
            xml_elements.append(f'<mxCell id="{node_id}" value="{label}" style="{style}" vertex="1" parent="1">')
            xml_elements.append(f'  <mxGeometry x="{x}" y="{y}" width="120" height="60" as="geometry" />')
            xml_elements.append('</mxCell>')
        
        # Add edges
        for i, edge in enumerate(edges):
            from_id = edge.get("from", "")
            to_id = edge.get("to", "")
            edge_label = edge.get("label", "")
            
            xml_elements.append(f'<mxCell id="edge_{i}" value="{edge_label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="{from_id}" target="{to_id}">')
            xml_elements.append('  <mxGeometry relative="1" as="geometry" />')
            xml_elements.append('</mxCell>')
        
        elements_xml = '\n        '.join(xml_elements)
        
        return f"""<mxfile>
  <diagram name="Diagram">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {elements_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
