# -*- coding: utf-8 -*-
"""
Simple Web Demo - Streamlit
"""

import streamlit as st
import json
import sys
sys.path.insert(0, '.')

from src.engine.highway_calculator import HighwayCalculator, create_sample_data


def main():
    st.title("🛣️ Highway Parameter Engine")
    st.markdown("公路参数化计算演示")
    
    # 侧边栏
    st.sidebar.header("路线参数")
    
    # 示例数据或自定义
    use_sample = st.sidebar.checkbox("使用示例数据", value=True)
    
    if use_sample:
        data = create_sample_data()
        st.sidebar.success("已加载示例数据")
    else:
        st.sidebar.info("请先上传参数文件")
    
    # 显示参数
    with st.expander("查看路线参数"):
        st.json(data)
    
    # 计算选项
    st.header("坐标计算")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        calc_type = st.selectbox("计算类型", ["单点", "批量", "LOD", "横断面"])
    
    if calc_type == "单点":
        stake_input = st.text_input("桩号", "K0+500")
        
        if st.button("计算"):
            calc = HighwayCalculator()
            calc.load_from_json(data)
            
            # 解析桩号
            s = calc._parse_stake(stake_input)
            result = calc.calculate_3d(s)
            
            st.success("计算完成")
            st.write("### 结果")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("桩号", result['stake'])
            col2.metric("X", result['x'])
            col3.metric("Y", result['y'])
            col4.metric("Z", result['z'])
            st.metric("方位角", f"{result['azimuth']}°")
    
    elif calc_type == "批量":
        start_stake = st.text_input("起点桩号", "K0+000")
        end_stake = st.text_input("终点桩号", "K1+000")
        interval = st.slider("间隔(m)", 10, 200, 100)
        
        if st.button("批量计算"):
            calc = HighwayCalculator()
            calc.load_from_json(data)
            
            s1 = calc._parse_stake(start_stake)
            s2 = calc._parse_stake(end_stake)
            
            results = calc.calculate_range(s1, s2, interval)
            
            st.success(f"计算完成: {len(results)} 个点")
            
            # 显示表格
            import pandas as pd
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            
            # 下载
            csv = df.to_csv(index=False)
            st.download_button("下载CSV", csv, "highway_coords.csv", "text/csv")
    
    elif calc_type == "LOD":
        lod_level = st.select_slider("LOD级别", ["LOD0", "LOD1", "LOD2"], value="LOD1")
        start_stake = st.text_input("起点", "K0+000")
        end_stake = st.text_input("终点", "K0+500")
        
        if st.button("LOD计算"):
            calc = HighwayCalculator()
            calc.load_from_json(data)
            
            s1 = calc._parse_stake(start_stake)
            s2 = calc._parse_stake(end_stake)
            
            results = calc.calculate_lod(s1, s2, lod_level)
            
            st.success(f"LOD{lod_level[-1]}: {len(results)} 个点")
            import pandas as pd
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
    
    elif calc_type == "横断面":
        stake = st.text_input("桩号", "K0+500")
        offset = st.slider("横向偏移(m)", -20, 20, 0)
        
        if st.button("计算横断面"):
            calc = HighwayCalculator()
            calc.load_from_json(data)
            
            s = calc._parse_stake(stake)
            cs = calc.calculate_cross_section(s, offset)
            
            st.write("### 横断面结果")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**中心点**")
                st.write(f"X: {cs['center']['x']:.3f}")
                st.write(f"Y: {cs['center']['y']:.3f}")
                st.write(f"Z: {cs['center']['z']:.3f}")
            
            with col2:
                st.write("**左侧点**")
                st.write(f"X: {cs['left']['x']:.3f}")
                st.write(f"Y: {cs['left']['y']:.3f}")
                st.write(f"Z: {cs['left']['z']:.3f}")
            
            with col3:
                st.write("**右侧点**")
                st.write(f"X: {cs['right']['x']:.3f}")
                st.write(f"Y: {cs['right']['y']:.3f}")
                st.write(f"Z: {cs['right']['z']:.3f}")
            
            st.metric("路基宽度", f"{cs['width']}m")
            st.metric("超高", f"{cs['superelevation']}%")


if __name__ == "__main__":
    main()
