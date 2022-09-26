Just my personal wireguard setup.
A publicly accesible server is hosting this python program which starts a
wireguard docker. Toml files in
> ~/.config/gateway/services/<SERVER>/<SERVICE>/.toml

determine which ports are forwarded to where. Example:
```toml
# main reverse proxy for all things web
name = "reverse_proxy"

[[expose]]
public = 80

[[expose]]
public = 443
```

will forward requests from port 80 and 443 to <SERVER>.
`internal` can also be specified to redirect the ports to other ports.
