"use client"

import { Save, Send, Mail, Merge } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Friend } from "./types"

interface ChatDialogsProps {
    // Profile
    profileOpen: boolean
    setProfileOpen: (open: boolean) => void
    selectedFriend?: Friend

    // Edit Message
    editingMessage: { id: string, content: string } | null
    setEditingMessage: (msg: { id: string, content: string } | null) => void
    onSaveEditedMessage: () => void
    onSendEditedToFriend: () => void

    // Email
    emailDialogOpen: boolean
    setEmailDialogOpen: (open: boolean) => void
    emailForm: { to: string, cc: string, bcc: string, subject: string, content: string }
    setEmailForm: (form: { to: string, cc: string, bcc: string, subject: string, content: string }) => void
    onSendEmail: () => void

    // New Conversation
    isNewConversationDialogOpen: boolean
    setIsNewConversationDialogOpen: (open: boolean) => void
    newConversationTitle: string
    setNewConversationTitle: (title: string) => void
    onCreateConversation: () => void

    // Merge
    isMergeDialogOpen: boolean
    setIsMergeDialogOpen: (open: boolean) => void
    mergeTargetId: string
    setMergeTargetId: (id: string) => void
    onMergeConversation: () => void
    selectedConversationId: string
}

export function ChatDialogs({
    profileOpen,
    setProfileOpen,
    selectedFriend,
    editingMessage,
    setEditingMessage,
    onSaveEditedMessage,
    onSendEditedToFriend,
    emailDialogOpen,
    setEmailDialogOpen,
    emailForm,
    setEmailForm,
    onSendEmail,
    isNewConversationDialogOpen,
    setIsNewConversationDialogOpen,
    newConversationTitle,
    setNewConversationTitle,
    onCreateConversation,
    isMergeDialogOpen,
    setIsMergeDialogOpen,
    mergeTargetId,
    setMergeTargetId,
    onMergeConversation,
    selectedConversationId
}: ChatDialogsProps) {
    const btnPrimary = "bg-emerald-600 hover:bg-emerald-700 text-white"
    const btnSecondary = "bg-slate-800 hover:bg-slate-700 text-white"
    const btnSuccess = "bg-blue-600 hover:bg-blue-700 text-white"

    return (
        <>
            {/* Profile Dialog */}
            <Dialog open={profileOpen} onOpenChange={setProfileOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-white text-lg">Profile</DialogTitle>
                    </DialogHeader>
                    {selectedFriend && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <Avatar className="h-20 w-20 ring-4 ring-slate-700">
                                    <AvatarImage src={selectedFriend.avatar} />
                                    <AvatarFallback className="bg-slate-700 text-white text-2xl">{selectedFriend.name[0]}</AvatarFallback>
                                </Avatar>
                                <div>
                                    <h3 className="text-xl font-bold text-white">{selectedFriend.name}</h3>
                                    <Badge className={`mt-1 text-xs ${selectedFriend.status === 'online' ? 'bg-emerald-600/20 text-emerald-400' : selectedFriend.status === 'away' ? 'bg-amber-600/20 text-amber-400' : 'bg-slate-600/20 text-slate-400'}`}>
                                        {selectedFriend.status}
                                    </Badge>
                                </div>
                            </div>
                            <div className="space-y-4 bg-slate-800/50 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div><p className="text-xs text-slate-500 uppercase mb-1">Email</p><p className="text-sm text-white">{selectedFriend.email}</p></div>
                                    <div><p className="text-xs text-slate-500 uppercase mb-1">Phone</p><p className="text-sm text-white">{selectedFriend.phone || "Not set"}</p></div>
                                    <div><p className="text-xs text-slate-500 uppercase mb-1">Location</p><p className="text-sm text-white">{selectedFriend.location || "Not set"}</p></div>
                                    <div><p className="text-xs text-slate-500 uppercase mb-1">Joined</p><p className="text-sm text-white">{selectedFriend.joinedDate || "Unknown"}</p></div>
                                </div>
                                <div><p className="text-xs text-slate-500 uppercase mb-1">Bio</p><p className="text-sm text-slate-300">{selectedFriend.bio || "No bio available"}</p></div>
                            </div>
                            <DialogFooter>
                                <Button onClick={() => setProfileOpen(false)} className={btnSecondary}>Close</Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Edit Message Dialog */}
            <Dialog open={!!editingMessage} onOpenChange={() => setEditingMessage(null)}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="text-white">Edit Message</DialogTitle>
                        <DialogDescription className="text-slate-400">Modify the AI response before saving or sending</DialogDescription>
                    </DialogHeader>
                    {editingMessage && (
                        <div className="space-y-4">
                            <Textarea
                                value={editingMessage.content}
                                onChange={(e) => setEditingMessage({ ...editingMessage, content: e.target.value })}
                                className="min-h-[150px] bg-slate-800 border-slate-700 text-white"
                            />
                            <DialogFooter className="flex gap-2">
                                <Button onClick={() => setEditingMessage(null)} className={btnSecondary}>Cancel</Button>
                                <Button onClick={onSaveEditedMessage} className={btnPrimary}><Save className="h-4 w-4 mr-2" /> Save</Button>
                                {selectedFriend && (
                                    <Button onClick={onSendEditedToFriend} className={btnSuccess}><Send className="h-4 w-4 mr-2" /> Send to {selectedFriend.name.split(' ')[0]}</Button>
                                )}
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Email Dialog */}
            <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="text-white">Compose Email</DialogTitle>
                        <DialogDescription className="text-slate-400">Send this message as an email</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="grid gap-4">
                            <div><Label className="text-slate-300 text-sm">To *</Label><Input value={emailForm.to} onChange={(e) => setEmailForm({ ...emailForm, to: e.target.value })} placeholder="recipient@email.com" className="bg-slate-800 border-slate-700 text-white" /></div>
                            <div className="grid grid-cols-2 gap-3">
                                <div><Label className="text-slate-300 text-sm">CC</Label><Input value={emailForm.cc} onChange={(e) => setEmailForm({ ...emailForm, cc: e.target.value })} placeholder="cc@email.com" className="bg-slate-800 border-slate-700 text-white" /></div>
                                <div><Label className="text-slate-300 text-sm">BCC</Label><Input value={emailForm.bcc} onChange={(e) => setEmailForm({ ...emailForm, bcc: e.target.value })} placeholder="bcc@email.com" className="bg-slate-800 border-slate-700 text-white" /></div>
                            </div>
                            <div><Label className="text-slate-300 text-sm">Subject *</Label><Input value={emailForm.subject} onChange={(e) => setEmailForm({ ...emailForm, subject: e.target.value })} placeholder="Email subject" className="bg-slate-800 border-slate-700 text-white" /></div>
                            <div><Label className="text-slate-300 text-sm">Message</Label><Textarea value={emailForm.content} onChange={(e) => setEmailForm({ ...emailForm, content: e.target.value })} className="min-h-[120px] bg-slate-800 border-slate-700 text-white" /></div>
                        </div>
                        <DialogFooter>
                            <Button onClick={() => setEmailDialogOpen(false)} className={btnSecondary}>Cancel</Button>
                            <Button onClick={onSendEmail} disabled={!emailForm.to || !emailForm.subject} className={btnSuccess}><Mail className="h-4 w-4 mr-2" /> Send Email</Button>
                        </DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>

            {/* New Conversation Dialog */}
            <Dialog open={isNewConversationDialogOpen} onOpenChange={setIsNewConversationDialogOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-sm">
                    <DialogHeader>
                        <DialogTitle className="text-white">New Discussion</DialogTitle>
                        <DialogDescription className="text-slate-400">Create a new discussion branch</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-slate-300">Discussion Title</Label>
                            <Input
                                value={newConversationTitle}
                                onChange={(e) => setNewConversationTitle(e.target.value)}
                                placeholder="e.g., Project Sync, Bug Fixes"
                                className="bg-slate-800 border-slate-700 text-white"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button onClick={() => setIsNewConversationDialogOpen(false)} className={btnSecondary}>Cancel</Button>
                        <Button onClick={onCreateConversation} disabled={!newConversationTitle.trim()} className={btnPrimary}>Create</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Merge Dialog */}
            <Dialog open={isMergeDialogOpen} onOpenChange={setIsMergeDialogOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-sm">
                    <DialogHeader>
                        <DialogTitle className="text-white">Merge Discussion</DialogTitle>
                        <DialogDescription className="text-slate-400">
                            Merge <span className="text-white font-medium">{selectedFriend?.conversations.find(c => c.id === selectedConversationId)?.title}</span> into another discussion.
                            <br /><span className="text-amber-500 text-xs">Warning: The current discussion will be deleted after merging.</span>
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-slate-300">Target Discussion</Label>
                            <Select value={mergeTargetId} onValueChange={setMergeTargetId}>
                                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                                    <SelectValue placeholder="Select target..." />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-slate-700">
                                    {selectedFriend?.conversations
                                        .filter(c => c.id !== selectedConversationId && c.status !== 'merged')
                                        .map(conv => (
                                            <SelectItem key={conv.id} value={conv.id} className="text-white focus:bg-slate-800">
                                                {conv.title}
                                            </SelectItem>
                                        ))
                                    }
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button onClick={() => setIsMergeDialogOpen(false)} className={btnSecondary}>Cancel</Button>
                        <Button onClick={onMergeConversation} disabled={!mergeTargetId} className={btnPrimary}><Merge className="h-4 w-4 mr-2" /> Merge</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    )
}
