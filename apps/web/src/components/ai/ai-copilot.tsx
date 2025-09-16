'use client'

import * as React from 'react'
import { useState, useRef, useEffect } from 'react'
import {
  MessageCircle,
  Mic,
  MicOff,
  Send,
  Bot,
  User,
  Loader2,
  Lightbulb,
  Zap,
  Settings,
  X,
  Minimize2,
  Maximize2,
  Volume2,
  VolumeX,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Download
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Textarea,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  ScrollArea,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@originfd/ui'
import { cn } from '@/lib/utils'

// Types
interface AIMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  actions?: AIAction[]
  metadata?: {
    agent?: string
    tools_used?: string[]
    execution_time_ms?: number
    confidence?: number
    cost_psu?: number
  }
}

interface AIAction {
  id: string
  type: 'button' | 'link' | 'form' | 'code'
  label: string
  description?: string
  data?: any
  primary?: boolean
}

interface AISuggestion {
  id: string
  title: string
  description: string
  category: 'optimization' | 'assistance' | 'warning' | 'info'
  priority: 'high' | 'medium' | 'low'
  icon?: string
  action?: () => void
}

interface AIAgent {
  id: string
  name: string
  description: string
  status: 'idle' | 'thinking' | 'executing' | 'error'
  capabilities: string[]
  current_task?: string
}

// Inspector context
export interface InspectorContextValue {
  focusId: string | null
  setFocusId: (id: string | null) => void
}

export const InspectorContext = React.createContext<InspectorContextValue>({
  focusId: null,
  setFocusId: () => {}
})

// Mock AI Service
export class AICopilotService {
  private isConnected = false
  private agents: AIAgent[] = [
    {
      id: 'design-agent',
      name: 'Design Engineer',
      description: 'Validates designs and suggests optimizations',
      status: 'idle',
      capabilities: ['ODL-SD Validation', 'Energy Simulation', 'Cost Optimization']
    },
    {
      id: 'sales-agent',
      name: 'Sales Advisor',
      description: 'Handles quotes, ROI calculations, and proposals',
      status: 'idle',
      capabilities: ['ROI Analysis', 'Proposal Generation', 'Incentive Optimization']
    },
    {
      id: 'sourcing-agent',
      name: 'Sourcing Specialist',
      description: 'Manages procurement and supplier relationships',
      status: 'idle',
      capabilities: ['RFQ Generation', 'Supplier Matching', 'Logistics Optimization']
    }
  ]

  async connect(): Promise<boolean> {
    // Simulate connection
    await new Promise(resolve => setTimeout(resolve, 1000))
    this.isConnected = true
    return true
  }

  async sendMessage(message: string, context?: any): Promise<AIMessage> {
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500))

    const responses = [
      "I can help you with that! Let me analyze your project and suggest some optimizations.",
      "Based on your current design, I notice a few areas where we could improve efficiency.",
      "I've found some relevant components that might be better suited for your requirements.",
      "Let me run some simulations and get back to you with detailed recommendations."
    ]

    const randomResponse = responses[Math.floor(Math.random() * responses.length)]

    return {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: randomResponse,
      timestamp: new Date(),
      actions: [
        {
          id: 'action-1',
          type: 'button',
          label: 'Run Analysis',
          description: 'Analyze current project for optimization opportunities',
          primary: true
        },
        {
          id: 'action-2',
          type: 'button',
          label: 'Show Details',
          description: 'View detailed analysis results'
        }
      ],
      metadata: {
        agent: 'design-agent',
        tools_used: ['validate_odl_sd', 'simulate_energy'],
        execution_time_ms: 1500,
        confidence: 0.87,
        cost_psu: 3
      }
    }
  }

  async getContextualHelp(page: string, element?: string): Promise<AIMessage> {
    await new Promise(resolve => setTimeout(resolve, 800))

    const helpContent = `I can help you with the ${page} page. ${element ? `Specifically for the ${element} element, ` : ''}Here are some suggestions to get you started.`

    return {
      id: `help-${Date.now()}`,
      role: 'assistant',
      content: helpContent,
      timestamp: new Date(),
      actions: [
        {
          id: 'help-action-1',
          type: 'button',
          label: 'Show Tutorial',
          description: 'Walk through the key features'
        }
      ]
    }
  }

  async getSuggestions(): Promise<AISuggestion[]> {
    return [
      {
        id: 'suggestion-1',
        title: 'Optimize Component Layout',
        description: 'I noticed your current layout could be 15% more efficient',
        category: 'optimization',
        priority: 'high',
        icon: 'Zap'
      },
      {
        id: 'suggestion-2',
        title: 'Update Pricing Data',
        description: 'Component prices have changed since your last update',
        category: 'info',
        priority: 'medium',
        icon: 'RefreshCw'
      }
    ]
  }

  getAgents(): AIAgent[] {
    return this.agents
  }

  getConnectionStatus(): boolean {
    return this.isConnected
  }
}

const aiService = new AICopilotService()

interface AICopilotProps {
  className?: string
  defaultOpen?: boolean
}

export function AICopilot({ className, defaultOpen = false }: AICopilotProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<AIMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hi! I\'m your AI assistant. I can help you with component management, project optimization, and much more. What would you like to work on today?',
      timestamp: new Date(),
      actions: [
        {
          id: 'get-started',
          type: 'button',
          label: 'Get Started',
          description: 'Show me what you can do',
          primary: true
        }
      ]
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([])
  const [agents, setAgents] = useState<AIAgent[]>([])
  const [selectedTab, setSelectedTab] = useState('chat')
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [focusId, setFocusId] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const initializeAI = async () => {
      const connected = await aiService.connect()
      setIsConnected(connected)
      setAgents(aiService.getAgents())

      const initialSuggestions = await aiService.getSuggestions()
      setSuggestions(initialSuggestions)
    }

    initializeAI()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await aiService.sendMessage(inputMessage, { focusId })
      setMessages(prev => [...prev, response])
    } catch (error) {
      const errorMessage: AIMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const executeAction = async (action: AIAction) => {
    // Simulate action execution
    console.log('Executing action:', action)

    const responseMessage: AIMessage = {
      id: `action-response-${Date.now()}`,
      role: 'assistant',
      content: `Executed "${action.label}". ${action.description || 'Action completed successfully.'}`,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, responseMessage])
  }

  const startVoiceInput = () => {
    setIsListening(true)
    // TODO: Implement actual voice recognition
    setTimeout(() => {
      setIsListening(false)
      setInputMessage('Tell me about component optimization')
    }, 2000)
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const clearConversation = () => {
    setMessages([{
      id: 'welcome-new',
      role: 'assistant',
      content: 'Conversation cleared. How can I help you today?',
      timestamp: new Date()
    }])
  }

  const exportConversation = () => {
    const conversationData = {
      timestamp: new Date().toISOString(),
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
        metadata: m.metadata
      }))
    }

    const blob = new Blob([JSON.stringify(conversationData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai-conversation-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const provideFeedback = (messageId: string, positive: boolean) => {
    console.log('Feedback provided:', { messageId, positive })
    // TODO: Send feedback to AI service
  }

  if (!isOpen) {
    return (
      <InspectorContext.Provider value={{ focusId, setFocusId }}>
        <Button
          onClick={() => setIsOpen(true)}
          className={cn(
            "fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50",
            "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700",
            className
          )}
        >
          <Bot className="h-6 w-6" />
        </Button>
      </InspectorContext.Provider>
    )
  }

  return (
    <InspectorContext.Provider value={{ focusId, setFocusId }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className={cn(
          "fixed bottom-6 right-6 z-50",
          isMinimized ? "w-80 h-16" : "w-96 h-[600px]",
          className
        )}
      >
        <Card className="h-full flex flex-col shadow-2xl border-0 bg-white/95 backdrop-blur-sm">
        {/* Header */}
        <CardHeader className="pb-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bot className="h-5 w-5" />
              <CardTitle className="text-lg">AI Assistant</CardTitle>
              <span className="bg-white/20 text-white border-white/30 px-2 py-1 rounded text-sm">
                {isConnected ? 'Online' : 'Connecting...'}
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-white/20"
                onClick={toggleMute}
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-white/20"
                onClick={() => setIsMinimized(!isMinimized)}
              >
                {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-white hover:bg-white/20"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        {!isMinimized && (
          <CardContent className="flex-1 p-0 flex flex-col min-h-0">
            <Tabs value={selectedTab} onValueChange={setSelectedTab} className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-3 m-2">
                <TabsTrigger value="chat">Chat</TabsTrigger>
                <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                <TabsTrigger value="agents">Agents</TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 flex flex-col m-0 p-0">
                {/* Messages */}
                <div className="flex-1 p-4 overflow-y-auto">
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={cn(
                          "flex gap-3",
                          message.role === 'user' ? "justify-end" : "justify-start"
                        )}
                      >
                        {message.role !== 'user' && (
                          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center flex-shrink-0">
                            <Bot className="h-4 w-4 text-white" />
                          </div>
                        )}

                        <div
                          className={cn(
                            "max-w-[80%] rounded-lg p-3 space-y-2",
                            message.role === 'user'
                              ? "bg-blue-600 text-white"
                              : "bg-gray-100 text-gray-900"
                          )}
                        >
                          <p className="text-sm">{message.content}</p>

                          {message.actions && (
                            <div className="flex flex-wrap gap-2 pt-2">
                              {message.actions.map((action) => (
                                <Button
                                  key={action.id}
                                  variant={action.primary ? "default" : "outline"}
                                  size="sm"
                                  onClick={() => executeAction(action)}
                                  className="text-xs"
                                >
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                          )}

                          {message.metadata && (
                            <div className="flex items-center justify-between pt-2 text-xs opacity-70">
                              <div className="flex items-center space-x-2">
                                {message.metadata.agent && (
                                  <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">
                                    {message.metadata.agent}
                                  </span>
                                )}
                                {message.metadata.confidence && (
                                  <span>{Math.round(message.metadata.confidence * 100)}% confident</span>
                                )}
                              </div>
                              <div className="flex items-center space-x-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => provideFeedback(message.id, true)}
                                >
                                  <ThumbsUp className="h-3 w-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => provideFeedback(message.id, false)}
                                >
                                  <ThumbsDown className="h-3 w-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => navigator.clipboard.writeText(message.content)}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>

                        {message.role === 'user' && (
                          <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                            <User className="h-4 w-4 text-gray-600" />
                          </div>
                        )}
                      </div>
                    ))}

                    {isLoading && (
                      <div className="flex gap-3 justify-start">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                        <div className="bg-gray-100 rounded-lg p-3">
                          <div className="flex items-center space-x-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span className="text-sm text-gray-600">Thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 relative">
                      <Input
                        ref={inputRef}
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me anything..."
                        disabled={isLoading}
                        className="pr-12"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={startVoiceInput}
                        disabled={isLoading}
                      >
                        {isListening ? <MicOff className="h-4 w-4 text-red-500" /> : <Mic className="h-4 w-4" />}
                      </Button>
                    </div>
                    <Button
                      onClick={sendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      size="sm"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="text-xs text-gray-500">
                      Press Enter to send, Shift+Enter for new line
                    </div>
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearConversation}
                        className="text-xs h-6"
                      >
                        Clear
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={exportConversation}
                        className="text-xs h-6"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Export
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="suggestions" className="flex-1 p-4">
                <div className="space-y-3">
                  {suggestions.map((suggestion) => (
                    <Card key={suggestion.id} className="p-3">
                      <div className="flex items-start space-x-3">
                        <div className={cn(
                          "p-2 rounded-lg",
                          suggestion.category === 'optimization' && "bg-green-100 text-green-600",
                          suggestion.category === 'warning' && "bg-yellow-100 text-yellow-600",
                          suggestion.category === 'info' && "bg-blue-100 text-blue-600"
                        )}>
                          <Lightbulb className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{suggestion.title}</h4>
                          <p className="text-xs text-gray-600 mt-1">{suggestion.description}</p>
                          <div className="flex items-center justify-between mt-2">
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                suggestion.priority === 'high' && "border-red-200 text-red-600",
                                suggestion.priority === 'medium' && "border-yellow-200 text-yellow-600",
                                suggestion.priority === 'low' && "border-gray-200 text-gray-600"
                              )}
                            >
                              {suggestion.priority} priority
                            </Badge>
                            <Button size="sm" variant="outline" className="text-xs">
                              Apply
                            </Button>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="agents" className="flex-1 p-4">
                <div className="space-y-3">
                  {agents.map((agent) => (
                    <Card key={agent.id} className="p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-sm">{agent.name}</h4>
                          <p className="text-xs text-gray-600 mt-1">{agent.description}</p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {agent.capabilities.map((capability) => (
                              <Badge key={capability} variant="secondary" className="text-xs">
                                {capability}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge
                            variant={agent.status === 'idle' ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {agent.status}
                          </Badge>
                          <Button size="sm" variant="outline" className="text-xs">
                            Chat
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        )}
      </Card>
    </motion.div>
  </InspectorContext.Provider>
  )
}
