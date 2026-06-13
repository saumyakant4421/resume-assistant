class ConversationMemory:
    """Manage conversation context and resume data across interactions."""
    
    def __init__(self):
        self.resume_data = {}
        self.chat_history = []
        self.current_intent = ""
        self.last_subject = ""
        self.tool_usage = []
        self.decision_log = []
    
    def save_resume(self, data: dict) -> None:
        """Save extracted resume data."""
        self.resume_data = data
        self.chat_history = []  # Reset history when new resume is uploaded
        self.last_subject = ""
        self.tool_usage = []
        self.decision_log = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to chat history."""
        if not content:
            return
        
        self.chat_history.append({
            "role": role,
            "content": content
        })
        
        # Limit history to last 20 messages
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
    
    def get_context(self) -> dict:
        """Get current context: resume data and chat history."""
        return {
            "resume": self.resume_data,
            "history": self.chat_history,
            "message_count": len(self.chat_history),
            "last_subject": self.last_subject,
            "tool_usage": self.tool_usage,
            "decision_log": self.decision_log,
        }
    
    def set_intent(self, intent: str) -> None:
        """Set current detected intent."""
        self.current_intent = intent
    
    def set_last_subject(self, subject: str) -> None:
        """Remember the last subject discussed for follow-up questions."""
        self.last_subject = subject or ""

    def get_last_subject(self) -> str:
        """Get the most recent subject."""
        return self.last_subject

    def add_tool_usage(self, tool_name: str, intent: str = "", reason: str = "") -> None:
        """Record internal tool usage for traceability."""
        if not tool_name:
            return

        self.tool_usage.append({
            "tool_used": tool_name,
            "intent": intent,
            "reason": reason,
        })

        if len(self.tool_usage) > 20:
            self.tool_usage = self.tool_usage[-20:]

    def add_decision_log(self, intent: str, tool_used: str, reason: str) -> None:
        """Record the internal routing decision."""
        self.decision_log.append({
            "intent": intent,
            "tool_used": tool_used,
            "reason": reason,
        })

        if len(self.decision_log) > 20:
            self.decision_log = self.decision_log[-20:]
    
    def reset(self) -> None:
        """Reset all memory."""
        self.resume_data = {}
        self.chat_history = []
        self.current_intent = ""
        self.last_subject = ""
        self.tool_usage = []
        self.decision_log = []
    



# Global memory instance
memory = ConversationMemory()