import { ChevronsUpDown } from "lucide-react"
import * as React from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  getModelIdentity,
  parseModelIdentity,
  type LanguageModel,
} from "@/data/models"
import { cn } from "@/lib/utils"

interface ModelSelectorProps {
  models: LanguageModel[];
  value: string;
  onChange: (item: LanguageModel | null) => void;
  placeholder?: string;
}

export function ModelSelector({ 
  models, 
  value, 
  onChange, 
  placeholder = "Select a model..." 
}: ModelSelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [staleSelection, setStaleSelection] = React.useState(false)
  const [lastSelectedProvider, setLastSelectedProvider] = React.useState<string | null>(null)
  const selectedModel = React.useMemo(
    () => models.find((model) => getModelIdentity(model) === value) ?? null,
    [models, value]
  )
  const parsedSelection = React.useMemo(() => parseModelIdentity(value), [value])

  React.useEffect(() => {
    if (!value) {
      setStaleSelection(false)
      return
    }

    if (selectedModel) {
      setStaleSelection(false)
      setLastSelectedProvider(selectedModel.provider_key || selectedModel.provider)
      return
    }

    setStaleSelection(true)
  }, [selectedModel, value])

  return (
    <div className="space-y-1">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between bg-node border border-border"
          >
            <span className="text-subtitle">
              {selectedModel
                ? selectedModel.display_name
                : parsedSelection
                  ? `${parsedSelection.model_name} (Unavailable)`
                  : placeholder}
            </span>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full min-w-[350px] p-0 bg-node border border-border shadow-lg">
          <Command className="bg-node">
            <CommandInput placeholder="Search model..." className="h-9 bg-node" />
            <CommandList className="bg-node">
              <CommandEmpty>No model found.</CommandEmpty>
              <CommandGroup>
                {models.map((model) => {
                  const modelIdentity = getModelIdentity(model)
                  return (
                    <CommandItem
                      key={modelIdentity}
                      value={modelIdentity}
                      className={cn(
                        "cursor-pointer bg-node hover:bg-accent",
                        value === modelIdentity && "bg-blue-600/10 border-l-2 border-blue-500/50"
                      )}
                      onSelect={(currentValue) => {
                        if (currentValue === value) {
                          onChange(null)
                          setOpen(false)
                          return
                        }

                        const nextModel = models.find((item) => getModelIdentity(item) === currentValue)
                        if (!nextModel) {
                          setOpen(false)
                          return
                        }

                        if (staleSelection && lastSelectedProvider === "LMStudio") {
                          const confirmed = window.confirm(
                            "The selected LMStudio model is unavailable. Switch to this fallback model?"
                          )
                          if (!confirmed) {
                            setOpen(false)
                            return
                          }
                        }

                        onChange(nextModel)
                        setLastSelectedProvider(nextModel.provider_key || nextModel.provider)
                        setOpen(false)
                      }}
                    >
                      <div className="flex items-center justify-between w-full gap-3">
                        <div className="flex flex-col items-start min-w-0 flex-1">
                          <span className="text-title">{model.display_name}</span>
                          <span className="text-xs text-muted-foreground font-mono">{model.model_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {model.is_custom && (
                            <Badge className="text-xs text-amber-400 bg-amber-500/10 border-amber-500/30">
                              Custom
                            </Badge>
                          )}
                          {model.is_stale && (
                            <Badge className="text-xs text-amber-400 bg-amber-500/10 border-amber-500/30">
                              Stale
                            </Badge>
                          )}
                          <Badge className="text-xs text-primary bg-primary/10 border-primary/30 hover:bg-primary/20 hover:border-primary/50">
                            {model.provider}
                          </Badge>
                          {model.provider_key && model.provider_key !== model.provider && (
                            <Badge className="text-xs text-muted-foreground bg-muted/10 border-border">
                              {model.provider_key}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {staleSelection && (
        <p className="text-xs text-yellow-500">
          Selected model is unavailable for {parsedSelection?.provider_identity || lastSelectedProvider || 'this provider'}. Choose a replacement to continue.
        </p>
      )}
    </div>
  )
}
