{{- define "asset-database.fullname" -}}
{{- printf "%s-asset-database" .Values.environment }}
{{- end }}

{{- define "asset-database.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "asset-database.labels" -}}
helm.sh/chart: {{ include "asset-database.chart" . }}
app.kubernetes.io/name: {{ include "asset-database.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{ include "asset-database.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}


{{- define "asset-database.selectorLabels" -}}
backstage.uk/environment: {{ .Values.environment }}
backstage.uk/component: asset-database
{{- end }}
