/* Coach Spark - Final Production script.js */
document.addEventListener("DOMContentLoaded", () => {
  const employeeCard = document.getElementById("employee-card");
  const employeeSelect = document.getElementById("employee-select");
  const startBtn = document.getElementById("start-btn");
  const chatSection = document.getElementById("chat-section");
  const chatBox = document.getElementById("chat-box");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");

  let employeeId = "";

  const escapeHtml = (s)=>String(s).replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
  const scrollBottom=()=>chatBox.scrollTop=chatBox.scrollHeight;

  function appendMessage(kind,title,text){
    const card=document.createElement("div");
    card.className=kind==="user"?"user-message":"bot-message";
    card.innerHTML=`<div class="msg-title">${escapeHtml(title)}</div><div class="msg-body">${escapeHtml(text).replace(/\n/g,"<br>")}</div>`;
    chatBox.appendChild(card);
    scrollBottom();
  }

  function setBusy(busy){
    sendBtn.disabled=busy;
    input.disabled=busy;
    let load=document.getElementById("loading");
    if(busy){
      if(load) return;
      load=document.createElement("div");
      load.id="loading";
      load.className="bot-message loading";
      load.innerHTML="🔎 Searching knowledge base...<br>📘 Retrieving manuals...<br>🤖 Generating answer...";
      chatBox.appendChild(load);
    }else if(load){
      load.remove();
      input.focus();
    }
    scrollBottom();
  }

  function startSession(){
    employeeId=employeeSelect.value;
    if(!employeeId){ alert("Select an employee."); return; }
    employeeCard.classList.add("hidden");
    chatSection.classList.remove("hidden");
    appendMessage("bot","Coach Spark",
      "Welcome! Ask about safety, maintenance, SOPs, quality, machines or training.");
    input.focus();
  }

  async function sendMessage(){
    const message=input.value.trim();
    if(!message) return;
    appendMessage("user","You",message);
    input.value="";
    setBusy(true);
    try{
      const res=await fetch("/chat/",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({employee_id:employeeId,message})
      });
      const data=await res.json();
      setBusy(false);
      if(!res.ok||data.error){
        appendMessage("bot","Coach Spark",data.error||"Request failed.");
        return;
      }
      appendMessage("bot","Coach Spark",data.response||"No response received.");
    }catch(e){
      console.error(e);
      setBusy(false);
      appendMessage("bot","Coach Spark","Unable to connect to the server. Please try again.");
    }
  }

  startBtn?.addEventListener("click",startSession);
  sendBtn?.addEventListener("click",sendMessage);
  input?.addEventListener("keydown",e=>{
    if(e.key==="Enter"&&!e.shiftKey){
      e.preventDefault();
      sendMessage();
    }
  });
});





















// // =======================================
// // Coach Spark - Frontend Script
// // =======================================

// // Send message when Enter is pressed
// function handleKeyPress(event) {
//     if (event.key === "Enter") {
//         sendMessage();
//     }
// }

// const employeeProfiles = {

//     "E001":{
//         role:"Machine Technician",
//         department:"Maintenance"
//     },

//     "E002":{
//         role:"New Employee",
//         department:"Assembly"
//     },

//     "E003":{
//         role:"Quality Inspector",
//         department:"Quality"
//     },

//     "E004":{
//         role:"Forklift Operator",
//         department:"Logistics"
//     }

// };

// function updateEmployeeInfo(){

//     const id = document.getElementById("employeeSelect").value;

//     document.getElementById("employeeRole").value =
//         employeeProfiles[id].role;

//     document.getElementById("employeeDepartment").value =
//         employeeProfiles[id].department;

// }

// window.onload = updateEmployeeInfo;

// // =======================================
// // Send Message
// // =======================================

// async function sendMessage() {

//     const inputField = document.getElementById("userInput");
//     const sendBtn = document.getElementById("sendBtn");
//     const chatBox = document.getElementById("chatBox");

//     // Employee dropdown (add this in HTML)
//     const employeeSelect = document.getElementById("employeeSelect");
//     document.getElementById("employeePanel").style.display = "none";

//     const employeeId = employeeSelect.value;

//     const messageText = inputField.value.trim();

//     if (!messageText) return;

//     // Show user message
//     appendMessage(messageText, "user");

//     inputField.value = "";
//     inputField.disabled = true;
//     sendBtn.disabled = true;

//     // Loading bubble
//     const loadingDiv = document.createElement("div");
//     loadingDiv.className = "message assistant";
//     loadingDiv.id = "loadingBubble";

//     loadingDiv.innerHTML = `
//         <div class="bubble">
//             ⚙️ Coach Spark is thinking...
//         </div>
//     `;

//     chatBox.appendChild(loadingDiv);
//     chatBox.scrollTop = chatBox.scrollHeight;

//     try {

//         const response = await fetch("/api/chat/", {

//             method: "POST",

//             headers: {
//                 "Content-Type": "application/json"
//             },

//             body: JSON.stringify({

//                 message: messageText,
//                 employee_id: employeeId

//             })

//         });

//         const data = await response.json();

//         document.getElementById("loadingBubble").remove();

//         if (data.error) {

//             appendMessage(
//                 "Error: " + data.error,
//                 "assistant"
//             );

//             return;
//         }

//         appendMessage(

//             data.response,
//             "assistant",
//             data.tool_used,
//             data.sources || [],
//             data.section || ""

//         );

//     }
//     catch (err) {

//         if (document.getElementById("loadingBubble")) {
//             document.getElementById("loadingBubble").remove();
//         }

//         appendMessage(

//             "Unable to connect to the Django server.",

//             "assistant"

//         );

//     }
//     finally {

//         inputField.disabled = false;
//         sendBtn.disabled = false;
//         inputField.focus();

//     }

// }

// // =======================================
// // Append Chat Bubble
// // =======================================

// function appendMessage(

//     text,
//     sender,
//     toolUsed = null,
//     sources = [],
//     section = ""

// ) {

//     const chatBox = document.getElementById("chatBox");

//     const msgDiv = document.createElement("div");

//     msgDiv.className = `message ${sender}`;

//     let html = "";

//     // Tool Badge

//     if (toolUsed) {

//         html += `
//             <div class="tool-badge">
//                 🛠️ Tool Used:
//                 ${toolUsed}
//             </div>
//         `;

//     }

//     // Main Response

//     html += `
//         <div class="bubble">
//             ${text.replace(/\n/g, "<br>")}
//     `;

//     // Section

//     if (section) {

//         html += `
//             <hr>

//             <small>

//                 <strong>📑 Section:</strong>

//                 ${section}

//             </small>
//         `;

//     }

//     // // Sources

//     // if (sources.length > 0) {

//     //     html += `
//     //         <hr>

//     //         <small>

//     //             <strong>📘 Sources</strong>

//     //         </small>

//     //         <br>
//     //     `;

//     //     sources.forEach(source => {

//     //         html += `
//     //             <small>

//     //                 • ${source}

//     //             </small>

//     //             <br>
//     //         `;

//     //     });

//     // }

//     html += `</div>`;

//     msgDiv.innerHTML = html;

//     chatBox.appendChild(msgDiv);

//     chatBox.scrollTop = chatBox.scrollHeight;

// }
// body: JSON.stringify({

//     message: messageText,

//     employee_id: document.getElementById("employee").value

// })
