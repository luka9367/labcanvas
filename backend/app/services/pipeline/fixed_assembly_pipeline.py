"""Fixed Assembly mode pipeline - generates structured, editable diagrams."""

import json
import re
from typing import AsyncGenerator, List, Dict, Any

from app.services.pipeline.base import BasePipeline, PipelineContext, PipelineResult


class AssemblyPipeline(BasePipeline):
    """Assembly mode: 5-step pipeline for high-quality editable diagrams."""
    
    async def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute full assembly pipeline."""
        try:
            # Step 1: Plan
            plan = await self._step_plan(context)
            
            # Step 2: Generate concept image
            concept_image = await self._step_image(context, plan)
            
            # Step 3: Create blueprint
            blueprint = await self._step_blueprint(context, plan, concept_image)
            
            # Step 4: Generate components
            components = await self._step_components(context, blueprint)
            
            # Step 5: Final assembly
            final_xml = await self._step_assembly(context, blueprint, components)
            
            return PipelineResult(
                success=True,
                message="Assembly complete",
                data={
                    "xml": final_xml,
                    "concept_image": concept_image,
                    "blueprint": blueprint,
                    "components": components,
                    "mode": "assembly"
                }
            )
        except Exception as e:
            import traceback
            print(f"Assembly pipeline error: {e}")
            print(traceback.format_exc())
            return PipelineResult(
                success=False,
                message=f"Assembly failed: {str(e)}"
            )
    
    async def execute_stream(self, context: PipelineContext) -> AsyncGenerator[str, None]:
        """Execute with detailed progress streaming."""
        try:
            # Step 1
            yield json.dumps({"step": 1, "name": "plan", "message": "Analyzing requirements..."})
            plan = await self._step_plan(context)
            yield json.dumps({"step": 1, "name": "plan", "status": "complete", "data": plan})
            
            # Step 2
            yield json.dumps({"step": 2, "name": "image", "message": "Generating concept image..."})
            concept_image = await self._step_image(context, plan)
            yield json.dumps({"step": 2, "name": "image", "status": "complete", "data": concept_image})
            
            # Step 3
            yield json.dumps({"step": 3, "name": "blueprint", "message": "Creating blueprint..."})
            blueprint = await self._step_blueprint(context, plan, concept_image)
            yield json.dumps({"step": 3, "name": "blueprint", "status": "complete", "data": blueprint})
            
            # Step 4
            yield json.dumps({"step": 4, "name": "components", "message": "Generating components..."})
            components = await self._step_components(context, blueprint)
            yield json.dumps({"step": 4, "name": "components", "status": "complete", "data": components})
            
            # Step 5
            yield json.dumps({"step": 5, "name": "assembly", "message": "Assembling final diagram..."})
            final_xml = await self._step_assembly(context, blueprint, components)
            yield json.dumps({
                "step": 5,
                "name": "assembly",
                "status": "complete",
                "data": {
                    "xml": final_xml,
                    "concept_image": concept_image,
                    "mode": "assembly"
                }
            })
        except Exception as e:
            yield json.dumps({"step": "error", "message": str(e)})
    
    async def _step_plan(self, context: PipelineContext) -> Dict[str, Any]:
        """Step 1: Analyze and create plan."""
        system_prompt = """你是一个学术图表设计专家。分析用户需求并创建详细的设计方案。

设计时必须达到以下质量基准（参考优秀学术论文插图样张）：
- 视觉质量：高分辨率、线条清晰锐利
- 信息密度：高密度但不拥挤，包含3-6个主要模块，每个模块有详细子组件
- 模块数量：丰富的模块和流程框图，模块间有清晰的连接关系和数据流
- 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等）
- 整体风格：学术论文图表风格，手绘/卡通风格图标和插图，清晰的分块和边框
- 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
- 文字清晰度：所有标签必须清晰可读，字号层次分明

输出JSON格式：
{
    "title": "图表标题",
    "description": "整体描述",
    "sections": [
        {
            "name": "模块名称",
            "elements": ["元素1", "元素2"],
            "layout": "布局描述"
        }
    ],
    "style": {
        "color_scheme": "配色方案",
        "font": "字体建议",
        "overall_style": "整体风格"
    },
    "dimensions": {"width": 800, "height": 600}
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
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Extract JSON from markdown
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
                "description": context.prompt,
                "sections": [{"name": "主要流程", "elements": ["步骤1", "步骤2", "步骤3"], "layout": "horizontal"}],
                "style": {"color_scheme": "blue", "font": "Arial", "overall_style": "clean"},
                "dimensions": {"width": 800, "height": 600}
            }
    
    async def _step_image(self, context: PipelineContext, plan: Dict[str, Any]) -> str:
        """Step 2: Generate concept image."""
        try:
            # Create image prompt from plan
            image_prompt = f"""Academic paper illustration style diagram: {plan.get('title', 'Diagram')}

Description: {plan.get('description', context.prompt)}
Style: {plan.get('style', {}).get('overall_style', 'professional')}
Color scheme: {plan.get('style', {}).get('color_scheme', 'blue')}

Professional, clean, high-quality technical illustration suitable for academic publication.
Clear layout. White background. Minimal design.
"""
            
            result = await self.llm.generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard"
            )
            
            # Extract image URL - handle different response formats
            if isinstance(result, dict):
                data = result.get("data", [])
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0].get("url", "")
                # Alternative format
                if "url" in result:
                    return result["url"]
            
            return ""
        except Exception as e:
            print(f"Image generation error: {e}")
            return ""
    
    async def _step_blueprint(self, context: PipelineContext, plan: Dict[str, Any], concept_image: str) -> Dict[str, Any]:
        """Step 3: Create detailed blueprint."""
        system_prompt = """你是一个图表结构工程师。根据设计方案创建详细的结构蓝图。

设计时必须达到以下质量基准（参考优秀学术论文插图样张）：
- 视觉质量：高分辨率、线条清晰锐利
- 信息密度：高密度但不拥挤，包含3-6个主要模块，每个模块有详细子组件
- 模块数量：丰富的元素和流程框图，元素间有清晰的连接关系和数据流
- 色彩还原度：专业学术配色（蓝色、黄色、灰色、绿色、粉色等）
- 整体风格：学术论文图表风格，清晰的分块和边框
- 布局构图：清晰的分栏或分块布局，流程逻辑明确，留白合理
- 文字清晰度：所有标签必须清晰可读，字号层次分明

输出JSON格式：
{
    "canvas": {"width": 800, "height": 600},
    "elements": [
        {
            "id": "elem_1",
            "type": "box|text|arrow|image",
            "x": 100,
            "y": 100,
            "width": 120,
            "height": 60,
            "label": "标签文本",
            "style": {"fillColor": "#ffffff", "strokeColor": "#000000"}
        }
    ],
    "connections": [
        {"from": "elem_1", "to": "elem_2", "style": "arrow"}
    ]
}"""

        try:
            plan_json = json.dumps(plan, ensure_ascii=False)
            user_prompt = f"根据以下设计方案创建详细结构蓝图：\n\n{plan_json}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm.chat_completion(
                messages,
                temperature=0.3,
            )
            
            content = await self.llm.extract_xml_from_response(response)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Failed to parse blueprint JSON")
        except Exception as e:
            print(f"Blueprint generation error: {e}")
            # Return default blueprint
            return {
                "canvas": {"width": 800, "height": 600},
                "elements": [
                    {"id": "start", "type": "box", "x": 100, "y": 100, "width": 100, "height": 50, "label": "开始", "style": {"fillColor": "#e1f5fe"}},
                    {"id": "process", "type": "box", "x": 300, "y": 100, "width": 100, "height": 50, "label": "处理", "style": {"fillColor": "#fff3e0"}},
                    {"id": "end", "type": "box", "x": 500, "y": 100, "width": 100, "height": 50, "label": "结束", "style": {"fillColor": "#e8f5e9"}}
                ],
                "connections": [
                    {"from": "start", "to": "process", "style": "arrow"},
                    {"from": "process", "to": "end", "style": "arrow"}
                ]
            }
    
    async def _step_components(self, context: PipelineContext, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 4: Generate individual components."""
        components = []
        
        for elem in blueprint.get("elements", []):
            try:
                if elem.get("type") == "image":
                    # Generate image component
                    prompt = f"Simple icon for: {elem.get('label', 'component')}, flat design, white background, minimal"
                    try:
                        result = await self.llm.generate_image(prompt=prompt, size="512x512")
                        if isinstance(result, dict):
                            data = result.get("data", [])
                            if data and len(data) > 0:
                                elem["image_url"] = data[0].get("url", "")
                    except Exception as e:
                        print(f"Component image generation error: {e}")
                
                components.append(elem)
            except Exception as e:
                print(f"Component processing error: {e}")
                components.append(elem)
        
        return components
    
    async def _step_assembly(self, context: PipelineContext, blueprint: Dict[str, Any], components: List[Dict[str, Any]]) -> str:
        """Step 5: Assemble final XML."""
        system_prompt = """你是一个draw.io XML组装专家。根据结构蓝图生成完整的mxGraph XML。

要求：
1. 使用标准的mxGraph格式
2. 每个元素对应一个mxCell
3. 正确的几何位置和样式
4. 连接线使用edge="1"
5. 可以直接在draw.io中打开
6. 质量基准（参考优秀学术论文插图样张）：
   - 视觉质量：高分辨率、线条清晰锐利
   - 信息密度：高密度但不拥挤，包含3-6个主要模块
   - 模块数量：丰富的元素和流程框图，元素间有清晰的连接关系
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

        try:
            blueprint_json = json.dumps(blueprint, ensure_ascii=False)
            user_prompt = f"根据以下蓝图生成draw.io XML：\n\n{blueprint_json}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm.chat_completion(
                messages,
                temperature=0.3,
            )
            
            xml_content = await self.llm.extract_xml_from_response(response)
            
            # Clean up
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
            print(f"Assembly error: {e}")
            # Return default XML
            return """<mxfile>
  <diagram name="Diagram">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="start" value="开始" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="100" height="50" as="geometry" />
        </mxCell>
        <mxCell id="process" value="处理" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#fff3e0;" vertex="1" parent="1">
          <mxGeometry x="300" y="100" width="100" height="50" as="geometry" />
        </mxCell>
        <mxCell id="end" value="结束" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;" vertex="1" parent="1">
          <mxGeometry x="500" y="100" width="100" height="50" as="geometry" />
        </mxCell>
        <mxCell id="edge1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="start" target="process">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="edge2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="process" target="end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
