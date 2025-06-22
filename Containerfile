FROM workbench-images:cuda-c9s-py311-runtime-cudnn_2023c_20230922

LABEL name="workbench-images:cuda-comfyui-c9s-py311-manager"
LABEL summary="ComfyUI + Manager, CUDA, Python 3.11"
LABEL description="ComfyUI with node manager, CUDA ready, OpenShift compatible"
LABEL io.k8s.display-name="ComfyUI + Manager (CUDA, Python 3.11)"
LABEL authoritative-source-url="https://github.com/comfyanonymous/ComfyUI"

USER 0
WORKDIR /opt/app-root/bin/

COPY --chown=1001:0 os-packages.txt ./os-packages.txt
RUN if [ -s os-packages.txt ]; then \
      yum install -y $(cat os-packages.txt); \
    fi && \
    rm -f os-packages.txt && yum clean all && rm -rf /var/cache/dnf

USER 1001
WORKDIR /opt/app-root/src/

RUN git clone https://github.com/comfyanonymous/ComfyUI.git ComfyUI && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git ComfyUI/custom_nodes/ComfyUI-Manager

WORKDIR /opt/app-root/src/ComfyUI

COPY --chown=1001:0 requirements-comfyui.txt ./requirements-comfyui.txt
RUN pip install --upgrade pip && \
    if [ -f requirements-comfyui.txt ]; then pip install --no-cache-dir -r requirements-comfyui.txt; fi && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir gitpython aria2

RUN chmod -R g+w /opt/app-root/lib/python3.11/site-packages && fix-permissions /opt/app-root -P

COPY --chown=1001:0 start-comfyui-manager.sh /opt/app-root/src/ComfyUI/start-comfyui-manager.sh
RUN chmod +x /opt/app-root/src/ComfyUI/start-comfyui-manager.sh

WORKDIR /opt/app-root/src/ComfyUI
EXPOSE 8188

ENTRYPOINT ["./start-comfyui-manager.sh"]