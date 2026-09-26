import { FormEvent, ReactNode, useMemo, useState } from "react";

type IconName =
  | "activity"
  | "alert"
  | "bed"
  | "chevron"
  | "clock"
  | "dashboard"
  | "forecast"
  | "lock"
  | "logout"
  | "menu"
  | "plus"
  | "recommendation"
  | "search"
  | "settings"
  | "shield"
  | "sparkles"
  | "users";

type Department = {
  name: string;
  occupied: number;
  total: number;
  delta: number;
  color: string;
};

const departments: Department[] = [
  { name: "Emergency", occupied: 42, total: 48, delta: 8, color: "#f06449" },
  { name: "ICU", occupied: 26, total: 32, delta: 3, color: "#7c6be8" },
  { name: "General Ward", occupied: 94, total: 128, delta: -5, color: "#279f91" },
  { name: "Pediatrics", occupied: 31, total: 44, delta: 2, color: "#df9d31" },
];

const navItems: { id: string; label: string; icon: IconName }[] = [
  { id: "overview", label: "Overview", icon: "dashboard" },
  { id: "forecasts", label: "Forecasts", icon: "forecast" },
  { id: "anomalies", label: "Anomalies", icon: "alert" },
  { id: "recommendations", label: "Recommendations", icon: "recommendation" },
];

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    activity: <path d="M3 12h4l2.2-6 4.1 12 2.3-6H21" />,
    alert: (
      <>
        <path d="M10.3 3.4 2.4 17a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.4a2 2 0 0 0-3.4 0Z" />
        <path d="M12 9v4M12 17h.01" />
      </>
    ),
    bed: (
      <>
        <path d="M4 18v-8M20 18v-6a2 2 0 0 0-2-2H4v6h16" />
        <path d="M4 10V7h5a3 3 0 0 1 3 3" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="2" />
        <rect x="14" y="3" width="7" height="7" rx="2" />
        <rect x="3" y="14" width="7" height="7" rx="2" />
        <rect x="14" y="14" width="7" height="7" rx="2" />
      </>
    ),
    forecast: (
      <>
        <path d="M4 19V5M4 19h16" />
        <path d="m7 15 4-5 3 3 5-7" />
      </>
    ),
    lock: (
      <>
        <rect x="4" y="10" width="16" height="11" rx="3" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
      </>
    ),
    logout: (
      <>
        <path d="M10 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h5M14 8l4 4-4 4M18 12H9" />
      </>
    ),
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    plus: <path d="M12 5v14M5 12h14" />,
    recommendation: (
      <>
        <path d="M9 18h6M10 22h4" />
        <path d="M8.5 15.5A7 7 0 1 1 15.5 15.5c-.9.6-1.5 1.4-1.5 2.5h-4c0-1.1-.6-1.9-1.5-2.5Z" />
      </>
    ),
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),
    shield: <path d="M12 3 5 6v5c0 4.6 2.9 8.1 7 10 4.1-1.9 7-5.4 7-10V6l-7-3Z" />,
    sparkles: <><path d="m12 3 1 3.2L16 8l-3 1.8L12 13l-1-3.2L8 8l3-1.8L12 3Z" /><path d="m5 13 .7 2.3L8 16.5l-2.3 1.2L5 20l-.7-2.3L2 16.5l2.3-1.2L5 13ZM19 12l.5 1.5L21 14l-1.5.5L19 16l-.5-1.5L17 14l1.5-.5L19 12Z" /></>,
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 20v-2a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v2M16 4a3 3 0 0 1 0 6M17 13a5 5 0 0 1 4 4.9V20" />
      </>
    ),
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

function Logo() {
  return (
    <div className="logo">
      <span className="logo-mark"><span /><span /></span>
      <span>Pulse<span>Flow</span></span>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (role: ErpRole) => void }) {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    if (!data.get("username") || !data.get("password")) {
      setError("Please enter your username and password.");
      return;
    }
    onLogin(data.get("role") as ErpRole);
  }

  return (
    <main className="login-page">
      <div className="login-glow glow-one" />
      <div className="login-glow glow-two" />
      <section className="login-card">
        <div className="login-brand">
          <Logo />
          <span className="secure-chip"><Icon name="shield" size={14} /> Secure portal</span>
        </div>
        <div className="login-copy">
          <p className="eyebrow">Hospital operations intelligence</p>
          <h1>Welcome back.</h1>
          <p>Sign in to monitor patient flow, capacity, and clinical operations.</p>
        </div>
        <form onSubmit={submit}>
          <label>
            Username
            <span className="input-wrap">
              <Icon name="users" size={18} />
              <input name="username" placeholder="Enter your username" autoComplete="username" />
            </span>
          </label>
          <label>
            Password
            <span className="input-wrap">
              <Icon name="lock" size={18} />
              <input name="password" type={showPassword ? "text" : "password"} placeholder="Enter your password" autoComplete="current-password" />
              <button type="button" className="show-password" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "Hide" : "Show"}</button>
            </span>
          </label>
          <label>
            Demo role
            <span className="input-wrap">
              <Icon name="shield" size={18} />
              <select name="role" defaultValue="ADMIN">
                <option value="ADMIN">Administrator</option>
                <option value="DOCTOR">Doctor</option>
                <option value="HEAD_NURSE">Head nurse</option>
                <option value="PHARMACIST">Pharmacist</option>
                <option value="ACCOUNTANT">Accountant</option>
                <option value="RECEPTIONIST">Receptionist</option>
              </select>
            </span>
          </label>
          <div className="form-row">
            <label className="remember"><input type="checkbox" /> <span>Keep me signed in</span></label>
            <button type="button" className="text-button">Forgot password?</button>
          </div>
          {error && <p className="login-error">{error}</p>}
          <button className="depth-button" type="submit">
            <span>Sign in to dashboard</span>
            <Icon name="chevron" size={18} />
          </button>
        </form>
        <p className="login-footer"><Icon name="shield" size={15} /> Protected by enterprise-grade security</p>
      </section>
      <p className="page-copyright">© 2025 PulseFlow Health Systems</p>
    </main>
  );
}

function DepartmentCard({ item }: { item: Department }) {
  const percent = Math.round((item.occupied / item.total) * 100);
  return (
    <article className="department-card">
      <div className="department-top">
        <span className="department-icon" style={{ color: item.color, background: `${item.color}18` }}><Icon name="bed" /></span>
        <span className={`trend ${item.delta < 0 ? "down" : ""}`}>{item.delta > 0 ? "+" : ""}{item.delta}%</span>
      </div>
      <p>{item.name}</p>
      <div className="occupancy-number"><strong>{item.occupied}</strong><span>/ {item.total} beds</span></div>
      <div className="progress"><span style={{ width: `${percent}%`, background: item.color }} /></div>
      <div className="card-caption"><span>{percent}% occupied</span><span>{item.total - item.occupied} available</span></div>
    </article>
  );
}

function OccupancyChart() {
  const values = [64, 62, 67, 65, 70, 68, 73, 77, 74, 79, 76, 82, 80, 84, 81, 83, 79, 77, 81, 84, 86, 83, 85, 87];
  const points = values.map((v, i) => `${18 + i * 24},${205 - v * 1.65}`).join(" ");
  const area = `18,205 ${points} 570,205`;
  return (
    <div className="chart-wrap">
      <div className="y-labels"><span>100%</span><span>75%</span><span>50%</span><span>25%</span></div>
      <svg className="line-chart" viewBox="0 0 590 220" preserveAspectRatio="none">
        <defs>
          <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6558d9" stopOpacity=".22" />
            <stop offset="100%" stopColor="#6558d9" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[40, 90, 140, 190].map((y) => <line key={y} x1="18" x2="570" y1={y} y2={y} className="grid-line" />)}
        <polygon points={area} fill="url(#chartFill)" />
        <polyline points={points} className="chart-line" />
        <circle cx="570" cy={205 - values.at(-1)! * 1.65} r="5" className="chart-dot" />
      </svg>
      <div className="x-labels"><span>6 AM</span><span>10 AM</span><span>2 PM</span><span>6 PM</span><span>Now</span></div>
    </div>
  );
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [active, setActive] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const date = useMemo(() => new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric" }).format(new Date()), []);

  return (
    <div className="app-shell">
      <aside className={sidebarOpen ? "sidebar open" : "sidebar"}>
        <div className="sidebar-head"><Logo /><button className="mobile-close" onClick={() => setSidebarOpen(false)}>×</button></div>
        <nav>
          <p className="nav-label">Workspace</p>
          {navItems.map((item) => (
            <button key={item.id} className={active === item.id ? "nav-item active" : "nav-item"} onClick={() => { setActive(item.id); setSidebarOpen(false); }}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.id === "anomalies" && <b>3</b>}
            </button>
          ))}
          <p className="nav-label">Administration</p>
          <button className="nav-item"><Icon name="users" /><span>User management</span></button>
          <button className="nav-item"><Icon name="shield" /><span>Audit log</span></button>
          <button className="nav-item"><Icon name="settings" /><span>Settings</span></button>
        </nav>
        <div className="sidebar-security">
          <div className="security-title"><span><Icon name="shield" size={16} /></span><div><strong>Secure session</strong><small>Expires in 24:48</small></div></div>
          <div className="session-progress"><span /></div>
        </div>
        <div className="profile">
          <div className="avatar">AS</div>
          <div><strong>Arjun Sharma</strong><span>Administrator</span></div>
          <button onClick={onLogout} title="Log out"><Icon name="logout" size={18} /></button>
        </div>
      </aside>
      {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}

      <div className="main-panel">
        <header className="topbar">
          <button className="menu-button" onClick={() => setSidebarOpen(true)}><Icon name="menu" /></button>
          <div className="search"><Icon name="search" size={18} /><input placeholder="Search patients, units, reports..." /><kbd>⌘ K</kbd></div>
          <div className="topbar-actions">
            <span className="live-status"><i /> Systems operational</span>
            <button className="icon-button"><Icon name="alert" size={19} /><i /></button>
            <div className="role-badge">ADMIN</div>
          </div>
        </header>

        <main className="content">
          {active === "overview" ? (
            <>
              <div className="page-heading">
                <div><p className="date">{date}</p><h1>Good morning, Arjun.</h1><p>Here’s what’s happening across your hospital today.</p></div>
                <button className="depth-button compact"><span><Icon name="sparkles" size={18} /> Run AI pipeline</span></button>
              </div>

              <section className="summary-strip">
                <div><span className="summary-icon purple"><Icon name="bed" /></span><p>Total occupancy<strong>193 <small>/ 252 beds</small></strong></p><b className="metric">76.6%</b></div>
                <div><span className="summary-icon green"><Icon name="activity" /></span><p>Admissions today<strong>28 <small>patients</small></strong></p><b className="metric positive">+12%</b></div>
                <div><span className="summary-icon coral"><Icon name="clock" /></span><p>Average wait time<strong>18 <small>minutes</small></strong></p><b className="metric negative">+4 min</b></div>
              </section>

              <div className="section-heading"><div><h2>Department capacity</h2><p>Live bed availability by unit</p></div><button className="outline-button"><Icon name="plus" size={17} /> Update beds</button></div>
              <section className="department-grid">{departments.map((item) => <DepartmentCard key={item.name} item={item} />)}</section>

              <section className="lower-grid">
                <article className="panel chart-panel">
                  <div className="panel-heading"><div><h2>Hospital occupancy</h2><p>24-hour utilization trend</p></div><select aria-label="Chart period"><option>Today</option><option>This week</option></select></div>
                  <OccupancyChart />
                </article>
                <article className="panel priority-panel">
                  <div className="panel-heading"><div><h2>Priority alerts</h2><p>Requires your attention</p></div><button className="text-button">View all</button></div>
                  <div className="alert-list">
                    <div className="alert-row high"><span><Icon name="alert" size={18} /></span><div><strong>ER nearing capacity</strong><p>87.5% occupied · 6 beds left</p></div><small>8 min ago</small></div>
                    <div className="alert-row medium"><span><Icon name="forecast" size={18} /></span><div><strong>ICU surge predicted</strong><p>Expected +18% by 6 PM</p></div><small>22 min ago</small></div>
                    <div className="alert-row low"><span><Icon name="recommendation" size={18} /></span><div><strong>Transfer opportunity</strong><p>4 patients eligible for step-down</p></div><small>41 min ago</small></div>
                  </div>
                </article>
              </section>
            </>
          ) : (
            <section className="placeholder-page">
              <span><Icon name={navItems.find((item) => item.id === active)?.icon || "dashboard"} size={30} /></span>
              <p className="eyebrow">Operations workspace</p>
              <h1>{navItems.find((item) => item.id === active)?.label}</h1>
              <p>This workspace is ready for live hospital data and role-based workflows.</p>
              <button className="depth-button compact" onClick={() => setActive("overview")}><span>Return to overview</span></button>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

type ErpRole = "ADMIN" | "DOCTOR" | "HEAD_NURSE" | "PHARMACIST" | "ACCOUNTANT" | "RECEPTIONIST";
type ErpModule = "overview" | "patients" | "clinical" | "pharmacy" | "accounting" | "staff" | "reports";
type Patient = { name: string; id: string; unit: string; status: string; balance: number };

const erpRoleLabels: Record<ErpRole, string> = { ADMIN: "Administrator", DOCTOR: "Doctor", HEAD_NURSE: "Head nurse", PHARMACIST: "Pharmacist", ACCOUNTANT: "Accountant", RECEPTIONIST: "Receptionist" };
const erpAccess: Record<ErpRole, ErpModule[]> = {
  ADMIN: ["overview", "patients", "clinical", "pharmacy", "accounting", "staff", "reports"],
  DOCTOR: ["overview", "patients", "clinical", "reports"],
  HEAD_NURSE: ["overview", "patients", "clinical", "reports"],
  PHARMACIST: ["overview", "patients", "pharmacy", "reports"],
  ACCOUNTANT: ["overview", "patients", "accounting", "reports"],
  RECEPTIONIST: ["overview", "patients", "accounting", "reports"],
};
const erpModuleLabels: Record<ErpModule, string> = { overview: "Overview", patients: "Patients", clinical: "Clinical care", pharmacy: "Pharmacy & inventory", accounting: "Accounting", staff: "Staff & access", reports: "Reports" };
const erpPatients: Patient[] = [{ name: "Maya Patel", id: "PT-2048", unit: "ICU", status: "Treatment active", balance: 1840 }, { name: "Jon Bell", id: "PT-2047", unit: "Emergency", status: "Awaiting review", balance: 620 }, { name: "Aisha Khan", id: "PT-2044", unit: "Pediatrics", status: "Discharge ready", balance: 940 }];
const erpDepartments = [{ name: "Emergency", occupied: 42, total: 48, color: "#f06449" }, { name: "ICU", occupied: 26, total: 32, color: "#7c6be8" }, { name: "General ward", occupied: 94, total: 128, color: "#279f91" }, { name: "Pediatrics", occupied: 31, total: 44, color: "#df9d31" }];

function ErpHeading({ title, copy, eyebrow = "AI assisted hospital operations", action }: { title: string; copy: string; eyebrow?: string; action?: ReactNode }) { return <div className="page-heading"><div><p className="date">{eyebrow}</p><h1>{title}</h1><p>{copy}</p></div>{action}</div>; }

function ErpPatients({ patients, onAdd }: { patients: Patient[]; onAdd: (patient: Patient) => void }) {
  const [open, setOpen] = useState(false);
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); onAdd({ name: String(data.get("name")), id: `PT-${2050 + patients.length}`, unit: String(data.get("unit")), status: "Registration pending", balance: 0 }); setOpen(false); }
  return <><ErpHeading title="Patient registry" eyebrow="Patient administration" copy="Register patients, track care status, and keep each encounter connected to billing." /><section className="panel table-panel"><div className="panel-heading"><div><h2>Patient registry</h2><p>Demographics, care status, and open balance</p></div><button className="outline-button" onClick={() => setOpen(!open)}><Icon name="plus" size={16} /> Register patient</button></div>{open && <form className="inline-form" onSubmit={submit}><input name="name" required placeholder="Patient full name" /><select name="unit"><option>Emergency</option><option>ICU</option><option>General ward</option><option>Pediatrics</option></select><button className="small-action" type="submit">Add</button></form>}<div className="table-scroll"><table><thead><tr><th>Patient</th><th>Unit</th><th>Care status</th><th>Open balance</th></tr></thead><tbody>{patients.map((patient) => <tr key={patient.id}><td><strong>{patient.name}</strong><small>{patient.id}</small></td><td>{patient.unit}</td><td><span className="status-pill">{patient.status}</span></td><td>${patient.balance.toLocaleString()}</td></tr>)}</tbody></table></div></section><div className="module-grid"><ErpForm title="Appointment intake" copy="Capture a complete request at reception." fields={["Patient", "Appointment type", "Requested date"]} action="Save appointment" /><ErpForm title="Admission handoff" copy="Make the next action visible to every authorized team." fields={["Unit", "Priority", "Notes"]} action="Create handoff" /></div></>;
}

function ErpForm({ title, copy, fields, action }: { title: string; copy: string; fields: string[]; action: string }) { return <article className="panel form-panel"><h2>{title}</h2><p>{copy}</p>{fields.map((field) => <label key={field}>{field}{field === "Notes" ? <textarea placeholder="Enter details" /> : <input placeholder={`Enter ${field.toLowerCase()}`} type={field.includes("date") ? "date" : "text"} />}</label>)}<button className="small-action">{action}</button></article>; }

function ErpWorkspace({ role, onLogout }: { role: ErpRole; onLogout: () => void }) {
  const [active, setActive] = useState<ErpModule>("overview"); const [patients, setPatients] = useState(erpPatients); const [sidebarOpen, setSidebarOpen] = useState(false); const access = erpAccess[role];
  const go = (module: ErpModule) => { setActive(module); setSidebarOpen(false); };
  return <div className="app-shell"><aside className={sidebarOpen ? "sidebar open" : "sidebar"}><div className="sidebar-head"><Logo /><button className="mobile-close" onClick={() => setSidebarOpen(false)}>×</button></div><nav><p className="nav-label">Hospital workspace</p>{access.map((module) => <button key={module} className={active === module ? "nav-item active" : "nav-item"} onClick={() => go(module)}><Icon name={module === "accounting" ? "activity" : module === "clinical" ? "recommendation" : module === "pharmacy" ? "plus" : module === "staff" ? "shield" : module === "reports" ? "forecast" : module === "patients" ? "users" : "dashboard"} /><span>{erpModuleLabels[module]}</span>{module === "patients" && <b>{patients.length}</b>}</button>)}<p className="nav-label">Assistant</p><button className="nav-item" onClick={() => go("reports")}><Icon name="sparkles" /><span>AI recommendations</span></button></nav><div className="sidebar-security"><div className="security-title"><span><Icon name="shield" size={16} /></span><div><strong>Role-protected session</strong><small>{erpRoleLabels[role]}</small></div></div><div className="session-progress"><span /></div></div><div className="profile"><div className="avatar">{role.slice(0, 2)}</div><div><strong>{erpRoleLabels[role]}</strong><span>{role}</span></div><button onClick={onLogout} title="Log out"><Icon name="logout" size={18} /></button></div></aside>{sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}<div className="main-panel"><header className="topbar"><button className="menu-button" onClick={() => setSidebarOpen(true)}><Icon name="menu" /></button><div className="search"><Icon name="search" size={18} /><input placeholder="Search patients, units, reports..." /></div><div className="topbar-actions"><span className="live-status"><i /> Systems operational</span><div className="role-badge">{role}</div></div></header><main className="content">{active === "overview" && <ErpOverview role={role} patients={patients} go={go} />}{active === "patients" && <ErpPatients patients={patients} onAdd={(patient) => setPatients([...patients, patient])} />}{active === "clinical" && <ErpClinical role={role} patients={patients} />}{active === "pharmacy" && <ErpPharmacy role={role} />}{active === "accounting" && <ErpAccounting role={role} patients={patients} />}{active === "staff" && <ErpStaff role={role} />}{active === "reports" && <ErpReports />}</main></div></div>;
}

function ErpOverview({ role, patients, go }: { role: ErpRole; patients: Patient[]; go: (module: ErpModule) => void }) { return <><ErpHeading title={`Good morning, ${erpRoleLabels[role]}.`} copy="Capacity, care delivery, stock, and the money attached to each encounter." action={<button className="depth-button compact" onClick={() => go("reports")}><span><Icon name="sparkles" size={18} /> Run AI review</span></button>} /><section className="summary-strip"><div><span className="summary-icon purple"><Icon name="bed" /></span><p>Total occupancy<strong>193 <small>/ 252 beds</small></strong></p><b className="metric">76.6%</b></div><div><span className="summary-icon green"><Icon name="activity" /></span><p>Active patients<strong>{patients.length} <small>registered</small></strong></p><b className="metric positive">+12%</b></div><div><span className="summary-icon coral"><Icon name="clock" /></span><p>Today's charges<strong>$12,480 <small>posted</small></strong></p><b className="metric">98% collected</b></div></section><div className="section-heading"><div><h2>Department capacity</h2><p>Bed availability and care pressure</p></div><button className="outline-button" onClick={() => go("patients")}><Icon name="plus" size={17} /> Update workflow</button></div><section className="department-grid">{erpDepartments.map((item) => { const percent = Math.round(item.occupied / item.total * 100); return <article className="department-card" key={item.name}><div className="department-top"><span className="department-icon" style={{ color: item.color, background: `${item.color}18` }}><Icon name="bed" /></span><span className="trend">Live</span></div><p>{item.name}</p><div className="occupancy-number"><strong>{item.occupied}</strong><span>/ {item.total} beds</span></div><div className="progress"><span style={{ width: `${percent}%`, background: item.color }} /></div><div className="card-caption"><span>{percent}% occupied</span><span>{item.total - item.occupied} available</span></div></article>; })}</section><section className="lower-grid"><article className="panel chart-panel"><div className="panel-heading"><div><h2>Operations pulse</h2><p>Occupancy and collections over the last 24 hours</p></div><span className="status-pill">Stable</span></div><div className="metric-bars"><div><span>Bed utilization</span><strong>76%</strong><i><em style={{ width: "76%" }} /></i></div><div><span>Medicine issued</span><strong>64%</strong><i><em className="green-bar" style={{ width: "64%" }} /></i></div><div><span>Claims submitted</span><strong>88%</strong><i><em className="orange-bar" style={{ width: "88%" }} /></i></div></div></article><article className="panel priority-panel"><div className="panel-heading"><div><h2>AI attention queue</h2><p>Suggested next actions</p></div></div><div className="alert-list"><div className="alert-row high"><span><Icon name="alert" size={18} /></span><div><strong>ER nearing capacity</strong><p>6 beds left · review transfers</p></div></div><div className="alert-row medium"><span><Icon name="plus" size={18} /></span><div><strong>Insulin stock is low</strong><p>18 doses below reorder point</p></div></div><div className="alert-row low"><span><Icon name="recommendation" size={18} /></span><div><strong>3 invoices need coding</strong><p>Estimated value $2,140</p></div></div></div></article></section></>; }

function ErpClinical({ role, patients }: { role: ErpRole; patients: Patient[] }) { return <><ErpHeading title="Treatments & nursing tasks" eyebrow="Clinical care module" copy="Record the treatment delivered, medicine used, and next action. Each entry can become a ledger line." /><div className="module-grid"><ErpForm title="Record treatment" copy="Post the service delivered to an encounter." fields={["Patient", "Treatment or procedure", "Unit cost ($)", "Clinical note"]} action={role === "DOCTOR" ? "Sign clinical treatment" : "Save treatment draft"} /><article className="panel"><div className="panel-heading"><div><h2>Today's care log</h2><p>Recent treatments ready for review</p></div><span className="status-pill">4 entries</span></div><ul className="task-list"><li><span className="task-dot green-dot" /><div><strong>IV antibiotic · {patients[0].name}</strong><small>Dr. Sharma · 09:40 · $85 posted</small></div></li><li><span className="task-dot orange-dot" /><div><strong>Wound dressing · {patients[1].name}</strong><small>Pending nurse sign-off · $40</small></div></li><li><span className="task-dot purple-dot" /><div><strong>Vitals review · {patients[2].name}</strong><small>Stable · next check in 2 hours</small></div></li></ul></article></div></>; }

function ErpPharmacy({ role }: { role: ErpRole }) { return <><ErpHeading title="Medicine control" eyebrow="Pharmacy & inventory" copy="Issue medicine against a patient, see cost per dose, and reorder before care is interrupted." /><section className="inventory-grid">{[["Ceftriaxone 1g", 84, 30, 12.5], ["Insulin glargine", 18, 36, 24], ["Paracetamol 500mg", 240, 80, .25]].map(([name, stock, reorder, cost]) => <article className="panel inventory-card" key={String(name)}><div className="inventory-icon"><Icon name="plus" size={20} /></div><div><h2>{name}</h2><p>${Number(cost).toFixed(2)} per unit</p></div><strong className={Number(stock) < Number(reorder) ? "stock-low" : ""}>{stock}<small> units</small></strong><div className="progress"><span style={{ width: `${Math.min(Number(stock) / (Number(reorder) * 3) * 100, 100)}%` }} /></div><span className={Number(stock) < Number(reorder) ? "stock-label low-label" : "stock-label"}>{Number(stock) < Number(reorder) ? "Reorder suggested" : "Stock healthy"}</span></article>)}</section><div className="module-grid"><ErpForm title="Issue medicine" copy="Link medicine cost to a patient encounter." fields={["Patient", "Medicine", "Doses", "Route"]} action={role === "PHARMACIST" ? "Issue and post cost" : "Request medicine"} /><article className="panel"><h2>Stock movements</h2><p>Traceable activity for today</p><div className="movement"><span className="movement-plus">+</span><div><strong>24 Paracetamol received</strong><small>Purchase order PO-4408 · $6.00</small></div></div><div className="movement"><span className="movement-minus">−</span><div><strong>3 Ceftriaxone issued</strong><small>PT-2048 · treatment cost $37.50</small></div></div></article></div></>; }

function ErpAccounting({ role, patients }: { role: ErpRole; patients: Patient[] }) { const openBalance = patients.reduce((sum, patient) => sum + patient.balance, 0); return <><ErpHeading title="Accounting" eyebrow="Revenue cycle & cost control" copy="Connect beds, medicine, and treatment to an encounter amount so nothing delivered disappears from the ledger." /><section className="summary-strip"><div><span className="summary-icon purple"><Icon name="activity" /></span><p>Open patient balances<strong>${openBalance.toLocaleString()}</strong></p></div><div><span className="summary-icon green"><Icon name="plus" /></span><p>Medicine posted today<strong>$1,240</strong></p></div><div><span className="summary-icon coral"><Icon name="bed" /></span><p>Bed charges today<strong>$4,860</strong></p></div></section><section className="panel table-panel"><div className="panel-heading"><div><h2>Encounter ledger</h2><p>Medicine, treatment, and bed charges by patient</p></div><button className="outline-button"><Icon name="plus" size={16} /> New charge</button></div><div className="table-scroll"><table><thead><tr><th>Encounter</th><th>Bed charge</th><th>Medicine</th><th>Treatment</th><th>Total</th></tr></thead><tbody>{patients.map((patient, index) => { const bed = [420, 180, 260][index] || 100; const medicine = [37.5, 24, 12.5][index] || 10; const treatment = [85, 40, 60][index] || 35; return <tr key={patient.id}><td><strong>{patient.name}</strong><small>{patient.id} · {patient.unit}</small></td><td>${bed}.00</td><td>${medicine.toFixed(2)}</td><td>${treatment}.00</td><td><strong>${(patient.balance + bed + medicine + treatment).toFixed(2)}</strong></td></tr>; })}</tbody></table></div></section><div className="module-grid"><ErpForm title="Post a charge" copy="Use for a bed day, medicine, or completed treatment." fields={["Patient", "Charge type", "Amount ($)"]} action={role === "ACCOUNTANT" ? "Post to ledger" : "Submit for billing"} /><article className="panel"><h2>Controls</h2><p>AI helper checks before close of day.</p><ul className="task-list"><li><span className="task-dot green-dot" /><div><strong>All issued medicine linked</strong><small>98% of doses have a patient encounter</small></div></li><li><span className="task-dot orange-dot" /><div><strong>3 treatments missing codes</strong><small>Review before invoice export</small></div></li></ul></article></div></>; }

function ErpStaff({ role }: { role: ErpRole }) { return <><ErpHeading title="Staff & access" eyebrow="Administration" copy="Keep role access explicit and review actions that affect patients, inventory, and money." /><section className="panel table-panel"><div className="panel-heading"><div><h2>Team directory</h2><p>Least-privilege access for the hospital workspace</p></div><button className="outline-button"><Icon name="plus" size={16} /> Invite staff</button></div><div className="table-scroll"><table><thead><tr><th>Member</th><th>Role</th><th>Last activity</th><th>Access</th></tr></thead><tbody>{[["Arjun Sharma", "ADMIN", "Now", "All modules"], ["Dr. Priya Shah", "DOCTOR", "8 min ago", "Clinical + patients"], ["Nina Cole", "PHARMACIST", "14 min ago", "Pharmacy + patients"], ["Omar Lee", "ACCOUNTANT", "21 min ago", "Accounting + reports"]].map((member) => <tr key={member[0]}><td><strong>{member[0]}</strong></td><td><span className="role-badge inline-role">{member[1]}</span></td><td>{member[2]}</td><td>{member[3]}</td></tr>)}</tbody></table></div></section><article className="panel audit-panel"><h2>Recent audit activity</h2><p>Every sensitive change is attributable to a user and role.</p><div className="audit-line"><Icon name="shield" size={18} /><span><strong>{role}</strong> viewed the accounting ledger <small>just now</small></span></div><div className="audit-line"><Icon name="plus" size={18} /><span>Pharmacist issued 3 doses of Ceftriaxone <small>8 min ago</small></span></div></article></>; }

function ErpReports() { return <><ErpHeading title="Reports & recommendations" eyebrow="Decision support" copy="AI surfaces patterns and leaves the final decision with the accountable role." action={<button className="depth-button compact"><span><Icon name="sparkles" size={18} /> Refresh insights</span></button>} /><div className="report-grid"><article className="panel report-card featured"><span className="report-icon"><Icon name="sparkles" /></span><p className="eyebrow">Recommended action</p><h2>Prepare 4 step-down beds before 18:00</h2><p>ICU occupancy is 81% and the clinical queue shows four stable patients. Head nurse confirmation is required before movement.</p><button className="small-action">Review recommendation</button></article><article className="panel report-card"><span className="report-icon green-bg"><Icon name="forecast" /></span><h2>Seven-day capacity forecast</h2><strong>82% <small>peak occupancy</small></strong><p>ER demand is likely to rise 11% on Friday. Add one triage shift.</p></article><article className="panel report-card"><span className="report-icon orange-bg"><Icon name="activity" /></span><h2>Revenue integrity</h2><strong>96% <small>complete coding</small></strong><p>Three treatment notes need a billing code before invoice export.</p></article></div></>; }

export default function App() {
  const [role, setRole] = useState<ErpRole | null>(null);
  return role ? <ErpWorkspace role={role} onLogout={() => setRole(null)} /> : <Login onLogin={setRole} />;
}
