import React, { useEffect, useMemo, useState } from "react";
import QRCode from "qrcode";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";

const API = import.meta.env.VITE_API_URL || (window.location.port === "5173" ? "" : "http://localhost:8000");

// Màu sắc chuẩn CityEcho
const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa"];

interface Overview {
  total_plays: number;
  completed_plays: number;
  completion_rate: number;
  total_duration: number;
  sources: Record<string, number>;
  top_pois: Array<{ poi_id: string; name: string; plays: number }>;
  total_pois: number;
  published_pois: number;
  draft_pois: number;
  pending_pois: number;
}

interface PoiStats {
  by_status: Array<{ status: string; count: number }>;
  by_category: Array<{ category: string; count: number }>;
}

interface TimelineItem {
  date: string;
  plays: number;
}

interface VisitorSession {
  device_id: string;
  first_seen_at: string;
  last_seen_at: string;
  last_path: string;
  entry_source: "DIRECT" | "QR";
  is_active: boolean;
}

interface VisitorOverview {
  active_count: number;
  sessions: VisitorSession[];
}

interface Props {
  token: string;
  onError: (msg: string) => void;
}

const STATUS_LABEL: Record<string, string> = {
  PUBLISHED: "Đã xuất bản",
  DRAFT: "Bản nháp",
  PENDING: "Chờ duyệt",
  NEEDS_REVISION: "Cần sửa",
  ARCHIVED: "Lưu trữ",
};

const CATEGORY_LABEL: Record<string, string> = {
  campus: "Trường học",
  religious: "Tôn giáo",
  market: "Chợ",
  museum: "Bảo tàng",
  historical: "Lịch sử",
  "public-space": "Không gian công cộng",
};

export default function AnalyticsDashboard({ token, onError }: Props) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [poiStats, setPoiStats] = useState<PoiStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [visitors, setVisitors] = useState<VisitorOverview | null>(null);
  const [websiteQr, setWebsiteQr] = useState("");
  const [loading, setLoading] = useState(true);
  const [analyticsError, setAnalyticsError] = useState("");
  const [visitorsError, setVisitorsError] = useState("");

  const authHeaders = { Authorization: `Bearer ${token}` };
  const websiteUrl = useMemo(() => {
    const url = new URL(window.location.href);
    url.pathname = "/";
    url.search = "?join=1";
    url.hash = "";
    return url.toString();
  }, []);

  useEffect(() => {
    if (!token) return;
    let mounted = true;
    const loadAnalytics = async () => {
      const errors: string[] = [];
      const responses = await Promise.allSettled([
          fetch(`${API}/api/v1/admin/analytics/overview`, { headers: authHeaders }),
          fetch(`${API}/api/v1/admin/analytics/poi-stats`, { headers: authHeaders }),
          fetch(`${API}/api/v1/admin/analytics/events-timeline`, { headers: authHeaders }),
      ]);

      if (!mounted) return;

      const [overviewResult, poiStatsResult, timelineResult] = responses;
      if (overviewResult.status === "fulfilled") {
        if (overviewResult.value.ok) {
          setOverview((await overviewResult.value.json()) as Overview);
        } else {
          errors.push(`Tổng quan (${overviewResult.value.status})`);
        }
      } else {
        errors.push("Tổng quan (mất kết nối)");
      }

      if (poiStatsResult.status === "fulfilled") {
        if (poiStatsResult.value.ok) {
          setPoiStats((await poiStatsResult.value.json()) as PoiStats);
        } else {
          errors.push(`Thống kê POI (${poiStatsResult.value.status})`);
        }
      } else {
        errors.push("Thống kê POI (mất kết nối)");
      }

      if (timelineResult.status === "fulfilled") {
        if (timelineResult.value.ok) {
          setTimeline((await timelineResult.value.json()) as TimelineItem[]);
        } else {
          errors.push(`Biểu đồ lượt nghe (${timelineResult.value.status})`);
        }
      } else {
        errors.push("Biểu đồ lượt nghe (mất kết nối)");
      }

      setAnalyticsError(
        errors.length > 0
          ? `Một phần thống kê chưa tải được: ${errors.join(", ")}. Hệ thống sẽ tự thử lại sau 10 giây.`
          : "",
      );
      setLoading(false);
    };
    setLoading(true);
    void loadAnalytics();
    const intervalId = window.setInterval(loadAnalytics, 10_000);
    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let mounted = true;
    const loadVisitors = async () => {
      try {
        const response = await fetch(`${API}/api/v1/admin/analytics/visitor-sessions`, {
          headers: authHeaders,
        });
        if (!response.ok) throw new Error("Không thể tải trạng thái thiết bị truy cập");
        const data = (await response.json()) as VisitorOverview;
        if (mounted) {
          setVisitors(data);
          setVisitorsError("");
        }
      } catch (error) {
        if (mounted) {
          setVisitorsError(
            error instanceof TypeError
              ? "Mất kết nối máy chủ; trạng thái thiết bị sẽ tự thử lại sau 10 giây."
              : error instanceof Error
                ? error.message
                : "Không thể tải trạng thái thiết bị; hệ thống sẽ tự thử lại.",
          );
        }
      }
    };
    void loadVisitors();
    const intervalId = window.setInterval(loadVisitors, 10_000);
    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, [token]);

  useEffect(() => {
    QRCode.toDataURL(websiteUrl, {
      width: 220,
      margin: 2,
      color: { dark: "#102a43", light: "#ffffff" },
    })
      .then(setWebsiteQr)
      .catch(() => onError("Không thể tạo mã QR trang chủ"));
  }, [websiteUrl, onError]);

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="analytics-spinner" />
        <p>Đang tải dữ liệu thống kê...</p>
      </div>
    );
  }

  // Dữ liệu biểu đồ nguồn nghe
  const sourcesData = overview
    ? [
        { name: "GPS", value: overview.sources["GPS"] || 0 },
        { name: "QR Code", value: overview.sources["QR"] || 0 },
        { name: "Thủ công", value: overview.sources["MANUAL"] || 0 },
      ]
    : [];

  const totalSourcePlays = sourcesData.reduce((acc, d) => acc + d.value, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", marginTop: "10px" }}>
      {(analyticsError || visitorsError) && (
        <div role="status" style={{ padding: "10px 14px", borderRadius: "8px", background: "#fff5e5", color: "#8a5a16", fontSize: "13px" }}>
          {analyticsError || visitorsError}
        </div>
      )}
      {/* ─── KPI Metrics ─── */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "18px 20px", display: "flex", flexDirection: "column", gap: "4px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)" }}>
          <span style={{ font: "600 11px 'DM Mono', monospace", color: "#8c9998", letterSpacing: "1px", textTransform: "uppercase" }}>TỔNG LƯỢT NGHE</span>
          <strong style={{ font: "700 32px Fraunces, serif", color: "#102a43", lineHeight: 1.1, margin: "4px 0" }}>{overview?.total_plays ?? 0}</strong>
          <span style={{ fontSize: "11px", color: "#718385" }}>Lần kích hoạt thuyết minh</span>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "18px 20px", display: "flex", flexDirection: "column", gap: "4px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)" }}>
          <span style={{ font: "600 11px 'DM Mono', monospace", color: "#8c9998", letterSpacing: "1px", textTransform: "uppercase" }}>TỶ LỆ HOÀN TẤT</span>
          <strong style={{ font: "700 32px Fraunces, serif", color: "#1e8449", lineHeight: 1.1, margin: "4px 0" }}>{overview?.completion_rate ?? 0}%</strong>
          <span style={{ fontSize: "11px", color: "#718385" }}>{overview?.completed_plays ?? 0} lượt nghe hết câu chuyện</span>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "18px 20px", display: "flex", flexDirection: "column", gap: "4px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)" }}>
          <span style={{ font: "600 11px 'DM Mono', monospace", color: "#8c9998", letterSpacing: "1px", textTransform: "uppercase" }}>ĐỊA ĐIỂM XUẤT BẢN</span>
          <strong style={{ font: "700 32px Fraunces, serif", color: "#6366f1", lineHeight: 1.1, margin: "4px 0" }}>{overview?.published_pois ?? 0} <span style={{ fontSize: "16px", color: "#8c9998", fontWeight: 400 }}>/ {overview?.total_pois ?? 0}</span></strong>
          <span style={{ fontSize: "11px", color: "#718385" }}>Sẵn sàng phục vụ du khách</span>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "18px 20px", display: "flex", flexDirection: "column", gap: "4px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)" }}>
          <span style={{ font: "600 11px 'DM Mono', monospace", color: "#8c9998", letterSpacing: "1px", textTransform: "uppercase" }}>THỜI LƯỢNG PHÁT</span>
          <strong style={{ font: "700 32px Fraunces, serif", color: "#d76b43", lineHeight: 1.1, margin: "4px 0" }}>
            {overview ? Math.round((overview.total_duration || 0) / 60) : 0} <span style={{ fontSize: "16px", color: "#8c9998", fontWeight: 400 }}>phút</span>
          </strong>
          <span style={{ fontSize: "11px", color: "#718385" }}>Tổng thời lượng du khách lắng nghe</span>
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 8px" }}>Thiết bị đang truy cập</h3>
          <strong style={{ display: "block", font: "700 36px Fraunces, serif", color: "#1e8449" }}>{visitors?.active_count ?? 0}</strong>
          <p style={{ color: "#718385", fontSize: "12px", margin: "4px 0 14px" }}>
            Đếm profile trình duyệt có tín hiệu trong 1 phút gần nhất; tự cập nhật mỗi 10 giây. Profile đã từng vào lại sẽ được nhận diện, không tạo thiết bị mới.
          </p>
          {visitors && visitors.sessions.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
                <thead><tr><th>Trình duyệt</th><th>Nguồn</th><th>Truy cập gần nhất</th><th>Trạng thái</th></tr></thead>
                <tbody>
                  {visitors.sessions.map((session) => (
                    <tr key={session.device_id}>
                      <td title={session.device_id}>{session.device_id.slice(0, 8)}…</td>
                      <td>{session.entry_source === "QR" ? "QR" : "Trực tiếp"}</td>
                      <td>{new Date(session.last_seen_at).toLocaleString("vi-VN")}</td>
                      <td style={{ color: session.is_active ? "#1e8449" : "#899595", fontWeight: 700 }}>
                        {session.is_active ? "● Active" : "○ Offline"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p style={{ color: "#8c9998", fontSize: "12px" }}>Chưa ghi nhận thiết bị truy cập.</p>}
          <small style={{ display: "block", color: "#8c9998", marginTop: "10px" }}>
            Thiết bị tắt sẽ chuyển Offline sau tối đa 1 phút; bản ghi Offline vẫn hiện trong danh sách. Mỗi profile trên từng địa chỉ web được tính riêng; không lưu IP hay thông tin cá nhân.
          </small>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 8px" }}>QR tham gia CityEcho</h3>
          <p style={{ color: "#718385", fontSize: "12px", margin: "0 0 10px" }}>Quét mã để mở trang chủ trên điện thoại.</p>
          {websiteQr && <img src={websiteQr} alt="QR mở trang chủ CityEcho" width={180} height={180} />}
          <code style={{ fontSize: "11px", overflowWrap: "anywhere", color: "#718385" }}>{websiteUrl}</code>
          {websiteQr && (
            <a
              className="secondary"
              href={websiteQr}
              download="cityecho-website-qr.png"
              style={{ marginTop: "12px", textDecoration: "none" }}
            >
              Tải QR trang chủ
            </a>
          )}
          <small style={{ color: "#8c9998", marginTop: "8px" }}>
            Khi chạy local, hãy mở web bằng địa chỉ LAN hoặc domain để điện thoại quét được; mã localhost chỉ dùng trên chính máy đó.
          </small>
        </div>
      </section>

      {/* ─── Row 1: Top POI BarChart + Nguồn PieChart ─── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "20px" }}>
        {/* Top POI lượt nghe */}
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", minHeight: "300px" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 16px 0" }}>Top địa điểm được nghe nhiều nhất</h3>
          {overview && overview.top_pois.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={overview.top_pois}
                margin={{ top: 8, right: 16, left: 0, bottom: 40 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  angle={-20}
                  textAnchor="end"
                  interval={0}
                  height={45}
                />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", color: "#102a43" }}
                  labelStyle={{ color: "#d76b43", fontWeight: 600 }}
                />
                <Bar dataKey="plays" name="Lượt nghe" radius={[4, 4, 0, 0]}>
                  {overview.top_pois.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: "center", color: "#8c9998", fontSize: "12px", padding: "50px 20px" }}>Chưa có dữ liệu lượt nghe. Hãy thử "Mô phỏng GPS" trên trang khám phá.</div>
          )}
        </div>

        {/* Nguồn nghe PieChart */}
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", minHeight: "300px" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 16px 0" }}>Nguồn kích hoạt thuyết minh</h3>
          {totalSourcePlays > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={sourcesData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={88}
                  paddingAngle={3}
                  dataKey="value"
                  label={(props: any) =>
                    (props.percent ?? 0) > 0.05 ? `${props.name}: ${((props.percent ?? 0) * 100).toFixed(0)}%` : ""
                  }
                  labelLine={false}
                >
                  {sourcesData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", color: "#102a43" }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: "#64748b" }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: "center", color: "#8c9998", fontSize: "12px", padding: "50px 20px" }}>
              GPS: 0 · QR: 0 · Thủ công: 0
              <br />
              <small>Chưa có lượt nghe nào được ghi nhận.</small>
            </div>
          )}
        </div>
      </div>

      {/* ─── Row 2: Timeline + Trạng thái POI ─── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "20px" }}>
        {/* Timeline lượt nghe 7 ngày */}
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", minHeight: "260px" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 16px 0" }}>Lượt nghe 7 ngày gần nhất</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timeline} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(d) => d ? d.slice(5) : ""}
              />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", color: "#102a43" }}
              />
              <Line
                type="monotone"
                dataKey="plays"
                name="Lượt nghe"
                stroke="#d76b43"
                strokeWidth={2.5}
                dot={{ fill: "#d76b43", r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Trạng thái POI PieChart */}
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", minHeight: "260px" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 16px 0" }}>Phân bổ trạng thái POI</h3>
          {poiStats && poiStats.by_status.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={poiStats.by_status.map((d) => ({ ...d, name: STATUS_LABEL[d.status] || d.status }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={75}
                  dataKey="count"
                  label={(props: any) => `${props.name}: ${props.value ?? props.count}`}
                  labelLine={false}
                >
                  {poiStats.by_status.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", color: "#102a43" }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: "center", color: "#8c9998", fontSize: "12px", padding: "40px 20px" }}>Không có dữ liệu trạng thái POI.</div>
          )}
        </div>
      </div>

      {/* ─── Row 3: Danh mục POI BarChart ─── */}
      {poiStats && poiStats.by_category.length > 0 && (
        <div style={{ background: "#fff", border: "1px solid #e8e3da", borderRadius: "10px", padding: "20px 22px", boxShadow: "0 2px 8px rgba(16,42,69,0.04)", minHeight: "240px" }}>
          <h3 style={{ font: "600 16px Fraunces, serif", color: "#102a43", margin: "0 0 16px 0" }}>Phân bổ POI theo danh mục</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={poiStats.by_category.map((d) => ({
                ...d,
                label: CATEGORY_LABEL[d.category] || d.category,
              }))}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 16, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="label"
                tick={{ fontSize: 12, fill: "#64748b" }}
                width={120}
              />
              <Tooltip
                contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", color: "#102a43" }}
              />
              <Bar dataKey="count" name="Số POI" radius={[0, 4, 4, 0]}>
                {poiStats.by_category.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
