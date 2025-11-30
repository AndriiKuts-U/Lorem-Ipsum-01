import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Message = ({ message }) => {
    return (
        <div id={message.id} className={`message ${message.role}-message ${message.loading ? "loading" : ""} ${message.error ? "error" : ""}`}>
            {message.role === "bot" && <img className="avatar" src="/download.png" alt="Bot Avatar" />}
            <div className="text">
                {message.role === "bot" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                    </ReactMarkdown>
                ) : (
                    <p>{message.content}</p>
                )}
            </div>
        </div>
    );
};
export default Message;