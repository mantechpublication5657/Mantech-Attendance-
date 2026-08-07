/* ManTech HRMS Chatbot - chatbot.js
   Drop in: static/mantech_chatbot/js/chatbot.js
   Reads:   window.MT_CHAT_CONFIG  (injected by Django template)
*/

(function () {
  "use strict";

  /* ── Config (set by Django template via window.MT_CHAT_CONFIG) ── */
  const CFG = window.MT_CHAT_CONFIG || {};
  const USER_NAME = CFG.user_first_name || CFG.username || "Employee";
  const USER_INITIALS = USER_NAME.substring(0, 2).toUpperCase();

  /* ── Knowledge base ── */
  const KB = {
    "how_to_use": {
      text: "Here's a quick guide to <b>HRMS</b>:<br><br>" +
            "📋 <b>Attendance</b> — Mark, view & download reports<br>" +
            "💰 <b>Payroll</b> — View payslips & salary details<br>" +
            "📝 <b>Grievance</b> — Raise issues to HR<br>" +
            "🏖️ <b>Leave</b> — Apply and track leave requests<br>" +
            "👤 <b>Profile</b> — Update personal information<br><br>" +
            "Use the sidebar to navigate to any section.",
      qr: ["Mark attendance", "Download attendance", "Raise a grievance", "Payment issue", "Main menu"]
    },
    "mark_attendance": {
      text: "To <b>mark your attendance</b>:<br><ol>" +
            "<li>Go to <b>Attendance</b> in the sidebar.</li>" +
            "<li>Click <b>Mark Attendance</b>.</li>" +
            "<li>Allow location access if prompted.</li>" +
            "<li>You'll see a green tick.</li></ol><br>" +
            "⏰ Attendance window: <b>9:30 AM – 10:00 AM</b>.<br>" +
            "Late entries require manager approval.",
      qr: ["Download attendance", "Attendance dispute", "Main menu"]
    },
    "download_attendance": {
      text: "To <b>download your attendance report</b>:<br><ol>" +
            "<li>Go to <b>Attendance → Reports</b>.</li>" +
            "<li>Select the <b>Month</b> and <b>Year</b> Click Apply Filter.</li>" +
            "<li>Click <b>Download Attendance Report</b>.</li>" +
            "<li>The file downloads to your device instantly.</li></ol>",
      qr: ["Mark attendance", "Raise a grievance", "Main menu"]
    },
    "attendance_dispute": {
      text: "To raise an <b>attendance dispute</b>:<br><ol>" +
            "<li>Talk to <b>Manager for Dispute or Absent</b>.</li>" +
            "<li>You can also raise it as a Grievance if your manager is unresponsive.</li>"+
            "<li>Go to <b>Grievance → All Applications</b>.</li>" +
            "<li>Click <b>Select Attendance</b> in Issue Category.</li>" +
            "<li>Add a reason and submit.</li>" +
            "<li>Your manager will review within <b>1–2 working days</b>.</li></ol><br>" ,
      qr: ["Raise a grievance", "Download attendance", "Main menu"]
    },
    "raise_grievance": {
      text: "To <b>raise a grievance</b>:<br><ol>" +
            "<li>Click <b>Grievance</b> in the sidebar.</li>" +
            "<li>Click <b>All Applications</b>.</li>" +
            "<li>Click <b>New Grievance</b>.</li>" +
            "<li>Select category: <b>Attendance / Payment / Leave / Other</b>.</li>" +
            "<li>Describe your issue </li>" +
            "<li>Click <b>Submit</b> — your grievance is raised.</li></ol><br>" +
            "HR responds within <b>2–3 working days</b>.",
      qr: ["Payment issue", "Attendance dispute", "Main menu"]
    },
    "payment_issue": {
      text: "For a <b>payment or salary issue</b>:<br><ol>" +
            "<li>Go to <b>Your Profie </b> to review your payroll details.</li>" +
            "<li>If there is a discrepancy, go to <b>Grievance → All Applications</b> and click <b>New Grievance</b>.</li>" +
            "<li>Select category <b>Payment Issue</b>.</li>" +
            "<li>Describe the problem.</li>" +
            "<li>HR Finance will respond within <b>2–3 working days</b>.</li></ol>",
      qr: ["Download payslip", "Raise a grievance", "Main menu"]
    },
    "download_payslip": {
      text: "To <b>download your payslip</b>:<br><ol>" +
            "<li>Go to <b>Attendance → Scroll Down</b>.</li>" +
            "<li>Select the month you need.</li>" +
            "<li>Click the <b>Download Slip</b> button on the right.</li></ol><br>" +
            "<li>If not available, <b>Contact Manager</b>.</li></ol><br>" +
            "Payslips are available after the <b>1st of each month</b>.",
      qr: ["Payment issue", "Main menu"]
    },
    "leave_apply": {
      text: "To <b>apply for leave</b>:<br><ol>" +
            "<li>Go to <b>Grievance → All Applications → Add New" +
            "<li>Select leave type: Casual / Sick / Earned.</li>" +
            "<li>Write the date range and add a reason.</li>" +
            "<li>Click <b>Submit for Approval</b>.</li></ol><br>" +
            "Your manager will approve or reject. You'll get a notification.",
      qr: ["Leave balance", "Raise a grievance", "Main menu"]
    },
    "leave_balance": {
      text: "To check your <b>leave balance</b>:<br><ol>" +
            "<li>Go to <b>Employee → Section </b>from sidebar.</li>" +
            "<li>Your Casual, Sick, and Earned leave totals are shown.</li>" +
            "<li>You can also see leave history for the current year.</li></ol>",
      qr: ["Apply for leave", "Main menu"]
    },
    "profile_update": {
      text: "To <b>update your profile</b>:<br><ol>" +
            "<li>Click your name or avatar at the top right.</li>" +
            "<li>Select <b>My Profile</b>.</li>" +
            "<li>Edit your details and click <b>Save Changes</b>.</li></ol><br>" +
            "For changes to ID, bank details, or designation, raise a Grievance.",
      qr: ["Raise a grievance", "Main menu"]
    },
    "menu": {
      text: "I can help you with the following topics. Please choose one:",
      qr: ["How to use HRMS", "Mark attendance", "Download attendance", "Attendance dispute",
           "Raise a grievance", "Payment issue", "Download payslip", "Apply for leave", "Leave balance", "Update profile"]
    }
  };

  /* ── Intent matcher ── */
  const INTENTS = [
    { key: "mark_attendance",    patterns: ["mark attend", "punch in", "check in", "mark my attend"] },
    { key: "download_attendance",patterns: ["download attend", "export attend", "attendance report", "download report"] },
    { key: "attendance_dispute", patterns: ["attend disput", "wrong attend", "missing attend", "attend correct", "attend issue", "mismatch"] },
    { key: "raise_grievance",    patterns: ["griev", "complaint", "raise issue", "raise a griev", "submit griev"] },
    { key: "payment_issue",      patterns: ["salary", "pay issue", "payment issue", "pay problem", "salary issue", "wrong pay", "not received"] },
    { key: "download_payslip",   patterns: ["payslip", "pay slip", "salary slip", "download pay"] },
    { key: "leave_apply",        patterns: ["apply leave", "take leave", "leave apply", "request leave"] },
    { key: "leave_balance",      patterns: ["leave balance", "how many leave", "leave left", "leave available"] },
    { key: "profile_update",     patterns: ["update profile", "edit profile", "change profile", "my profile"] },
    { key: "how_to_use",         patterns: ["how to use", "guide", "tutorial", "get started", "help", "how does"] },
    { key: "menu",               patterns: ["menu", "main menu", "back", "options", "what can you"] },
  ];

  function matchIntent(text) {
    const t = text.toLowerCase();
    for (const intent of INTENTS) {
      if (intent.patterns.some(p => t.includes(p))) return intent.key;
    }
    return null;
  }

  /* ── DOM ── */
  let isOpen = false;
  let typingEl = null;

  const trigger   = document.getElementById("mt-chat-trigger");
  const tooltip   = document.getElementById("mt-chat-tooltip");
  const chatWin   = document.getElementById("mt-chat-window");
  const closeBtn  = document.getElementById("mt-close-btn");
  const msgsEl    = document.getElementById("mt-chat-messages");
  const qrEl      = document.getElementById("mt-quick-replies");
  const inputEl   = document.getElementById("mt-text-input");
  const sendBtn   = document.getElementById("mt-send-btn");
  const welcomeEl = document.getElementById("mt-welcome-bar");

  if (!trigger || !chatWin) return; // guard

  /* ── Inject username into welcome bar ── */
  if (welcomeEl) {
    welcomeEl.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>' +
      'Welcome back, <strong style="margin-left:3px; text-transform:capitalize;">' + USER_NAME + '</strong>! &nbsp;How can I help you today?';
  }

  /* ── Helpers ── */
  function scrollBottom() {
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  function addMsg(role, html) {
    const row = document.createElement("div");
    row.className = "mt-msg mt-" + role;

    const ava = document.createElement("div");
    ava.className = "mt-msg-avatar " + (role === "bot" ? "mt-bot-ico" : "mt-user-ico");
    ava.innerHTML = role === "bot"
      ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.38-1 1.73V7h1a7 7 0 0 1 7 7v1a2 2 0 0 1-2 2h-1v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-1H5a2 2 0 0 1-2-2v-1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2zm-3 9a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3zm6 0a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>'
      : USER_INITIALS;

    const bub = document.createElement("div");
    bub.className = "mt-bubble";
    bub.innerHTML = html;

    row.appendChild(ava);
    row.appendChild(bub);
    msgsEl.appendChild(row);
    scrollBottom();
    return row;
  }

  function showTyping() {
    if (typingEl) return;
    const row = document.createElement("div");
    row.className = "mt-msg mt-bot";
    row.innerHTML =
      '<div class="mt-msg-avatar mt-bot-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.38-1 1.73V7h1a7 7 0 0 1 7 7v1a2 2 0 0 1-2 2h-1v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-1H5a2 2 0 0 1-2-2v-1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2zm-3 9a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3zm6 0a1.5 1.5 0 0 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg></div>' +
      '<div class="mt-bubble"><div class="mt-typing"><span></span><span></span><span></span></div></div>';
    msgsEl.appendChild(row);
    typingEl = row;
    scrollBottom();
  }

  function hideTyping() {
    if (typingEl) { typingEl.remove(); typingEl = null; }
  }

  function setQRs(items) {
    qrEl.innerHTML = "";
    items.forEach(function (label) {
      const btn = document.createElement("button");
      btn.className = "mt-qr";
      btn.textContent = label;
      btn.addEventListener("click", function () { handleUser(label); });
      qrEl.appendChild(btn);
    });
  }

  function botReply(key) {
    const entry = KB[key] || KB["menu"];
    showTyping();
    setTimeout(function () {
      hideTyping();
      addMsg("bot", entry.text);
      setQRs(entry.qr || []);
    }, 750);
  }

  function handleUser(text) {
    if (!text.trim()) return;
    addMsg("user", text);
    setQRs([]);
    inputEl.value = "";

    /* map quick-reply labels to intent keys */
    const labelMap = {
      "how to use hrms":    "how_to_use",
      "mark attendance":    "mark_attendance",
      "download attendance":"download_attendance",
      "attendance dispute": "attendance_dispute",
      "raise a grievance":  "raise_grievance",
      "payment issue":      "payment_issue",
      "download payslip":   "download_payslip",
      "apply for leave":    "leave_apply",
      "leave balance":      "leave_balance",
      "update profile":     "profile_update",
      "main menu":          "menu",
    };
    const normalized = text.toLowerCase().trim();
    const key = labelMap[normalized] || matchIntent(text) || null;

    if (key) {
      botReply(key);
    } else {
      showTyping();
      setTimeout(function () {
        hideTyping();
        addMsg("bot",
          "I'm not sure about that. I can help with <b>attendance, payroll, leave, grievances,</b> and <b>profile</b> queries. Please choose from the options below. for further help, Please contact to your <b>Manager</b>.");
        setQRs(KB["menu"].qr);
      }, 600);
    }
  }

  /* ── Open / close ── */
  function openChat() {
    isOpen = true;
    chatWin.classList.add("mt-open");
    tooltip.style.display = "none";
    inputEl.focus();

    /* send welcome only once */
    if (!msgsEl.dataset.initialized) {
      msgsEl.dataset.initialized = "1";
      setTimeout(function () {
        addMsg("bot",
          "👋 Hello, <b style = 'text-transform:capitalize;'>" + USER_NAME + "</b>! I'm your HRMS assistant.<br><br>" +
          "I can help you with attendance, payroll, leaves, and grievances. What do you need?");
        setQRs(KB["menu"].qr);
      }, 300);
    }
  }

  function closeChat() {
    isOpen = false;
    chatWin.classList.remove("mt-open");
  }

  trigger.addEventListener("click", function () {
    isOpen ? closeChat() : openChat();
  });
  closeBtn.addEventListener("click", closeChat);

  /* ── Send ── */
  sendBtn.addEventListener("click", function () { handleUser(inputEl.value); });
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleUser(inputEl.value); }
  });

  /* ── Auto-hide tooltip after 6s ── */
  setTimeout(function () { tooltip.style.display = "none"; }, 6000);

})();
