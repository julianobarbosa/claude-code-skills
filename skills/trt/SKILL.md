skill_name: trt_metabolic_monitoring_and_microdosing_workflow
version: "1.0"
author: "AI Clinical Companion"
description: "Workflow operacional para análise laboratorial, cálculo de microdosagem/fracionamento androgênico com caneta de precisão e rastreamento de segurança cardiometabólica."

triggers:
  - "Análise de exames laboratoriais de rotina ou reposição hormonal"
  - "Cálculo de fracionamento de testosterona com canetas de injeção"
  - "Monitoramento de segurança metabólica em terapia androgênica"

baseline_data:
  patient_profile:
    age: 59[span_0](start_span)[span_0](end_span)
    baseline_date: "2026-08-19[span_1](start_span)"[span_1](end_span)
  critical_markers:
    hormonal:
      total_testosterone: 469.16 ng/dL[span_2](start_span)[span_2](end_span)
      free_testosterone: 17.21 ng/dL[span_3](start_span)[span_3](end_span)
      shbg: 6.5 nmol/L (severely suppressed)[span_4](start_span)[span_4](end_span)
      dhea_s: 47.39 mcg/dL[span_5](start_span)[span_5](end_span)
      psa_total: 2.52 ng/mL[span_6](start_span)[span_6](end_span)
    lipid_cardiovascular:
      hdl: 16 mg/dL (critical low)[span_7](start_span)[span_7](end_span)
      ldl: 164 mg/dL[span_8](start_span)[span_8](end_span)
      triglycerides: 205 mg/dL[span_9](start_span)[span_9](end_span)
      total_cholesterol: 221 mg/dL[span_10](start_span)[span_10](end_span)
    hematology_metabolism:
      hematocrit: 46.3%[span_11](start_span)[span_11](end_span)
      hemoglobin: 15.2 g/dL[span_12](start_span)[span_12](end_span)
      fasting_glucose: 89 mg/dL[span_13](start_span)[span_13](end_span)
      hba1c: 5.5%[span_14](start_span)[span_14](end_span)
      creatinine: 1.24 mg/dL[span_15](start_span)[span_15](end_span)
      vitamin_d3: 24.6 ng/mL[span_16](start_span)[span_16](end_span)
      vitamin_b12: 1029 pg/mL (elevated)[span_17](start_span)[span_17](end_span)
      serum_iron: 44 mcg/dL (low)[span_18](start_span)[span_18](end_span)
      ferritin: 60.45 ng/mL[span_19](start_span)[span_19](end_span)

workflow_steps:
  step_1_lab_analysis_and_triage:
    action: "Segmentar os biomarcadores por eixos fisiológicos e correlacionar com o uso de andrógenos."
    rules:
      - If "exogenous testosterone active":
          - Expect low SHBG (<15 nmol/L) and reduced DHEA-S[span_20](start_span)[span_20](end_span).
          - Flag high Free T:Total T ratio[span_21](start_span)[span_21](end_span).
      - If "HDL < 25 mg/dL" or "Triglycerides > 150 mg/dL":
          - Prioritize lipid risk stratification over isolated androgen optimization[span_22](start_span)[span_22](end_span).
      - If "B12 > Upper Reference":
          - Contraindicate further B12 supplementation[span_23](start_span)[span_23](end_span).

  step_2_microdosing_and_pen_calibration:
    action: "Calcular dosagem fracionada e conversão mecânica de cliques em dispositivos U-100."
    device_specs:
      pen_model: "Eli Lilly HumaPen Ergo II"
      standard: "U-100 (100 UI = 1.0 mL)"
      increment: "1 clique / 1 UI = 0.01 mL"
      max_dial: "60 UI (0.6 mL)"
    calculation_logic:
      original_protocol: "Deposteron 200 mg / 2.0 mL a cada 10 dias"
      target_frequency: "Every Other Day (Dia Sim, Dia Não - DSDN = 5 doses por ciclo de 10 dias)"
      volume_per_dose: "2.0 mL / 5 = 0.40 mL"
      dose_per_injection: "40 mg cipionato de testosterona"
      clicks_setting: "0.40 mL / 0.01 mL por clique = 40 Cliques (40 UI)"

  step_3_hardware_and_viscosity_validation:
    action: "Validar agulhas e dispositivos contra a viscosidade do veículo oleoso."
    safety_checks:
      - check_gauge:
          risk_item: "32G 4mm"
          issue: "Resistência extrema com óleo de amendoim; risco de quebra da caneta e nódulo subcutâneo superficial."
          recommendation: "Preferir agulhas 29G a 30G (8mm) para fluxo adequado em camada subcutânea profunda."
      - check_asepsis:
          protocol: "Transferência de ampola aberta para carpule de 3 mL via seringa descartável estéril (agulha 18G/22G)."

  step_4_actionable_supplementation_and_lifestyle:
    interventions:
      - target: "Triglicerídeos altos & HDL crítico[span_24](start_span)"[span_24](end_span)
        action: "Ômega-3 EPA/DHA (3–4 g/dia) + Treino aeróbico contínuo (Zona 2)"
      - target: "Vitamina D3 subótima (24.6 ng/mL)[span_25](start_span)"[span_25](end_span)
        action: "Vitamina D3 (2.000–5.000 UI/dia) + Vitamina K2 MK-7"
      - target: "Vitamina B12 elevada (1029 pg/mL)[span_26](start_span)"[span_26](end_span)
        action: "Interromper complexos multivitamínicos com B12[span_27](start_span)"[span_27](end_span)
      - target: "Ferro sérico limítrofe (44 mcg/dL)[span_28](start_span)"[span_28](end_span)
        action: "Monitorar ingestão dietética e ferritina sérica (não sobrecarregar)[span_29](start_span)"[span_29](end_span)

  step_5_longitudinal_tracking_and_red_flags:
    follow_up_window: "60 a 90 dias"
    red_flag_triggers:
      - "Hematócrito > 52% (risco de eritrocitose e hiperviscosidade)"
      - "PSA Total > 4.0 ng/mL ou aumento anual rápido[span_30](start_span)"[span_30](end_span)
      - "HDL persistentemente < 20 mg/dL[span_31](start_span)"[span_31](end_span)
      - "Formação de granulomas ou dor inflamatória no local da injeção subcutânea"
      
